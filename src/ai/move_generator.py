"""
生成所有合法出牌
"""
from typing import List, Optional
from collections import Counter
from itertools import combinations

from src.game.card import Card, sort_cards, count_card_ranks
from src.game.move_validator import (
    analyze_hand,
    PlayResult,
    can_beat,
    CARD_ORDER,
    JOKER_SMALL,
    JOKER_BIG,
)


class MoveGenerator:
    """出牌生成器"""

    def __init__(self):
        pass

    def generate_all_moves(self, cards: List[Card], last_play: Optional[List[Card]] = None) -> List[List[Card]]:
        """
        生成所有合法出牌

        Args:
            cards: 手牌
            last_play: 上家出的牌, None表示可以出任意牌

        Returns:
            合法出牌列表
        """
        if not cards:
            return []

        cards = sort_cards(cards)
        all_moves = []

        # 如果没有上家出牌,生成所有可能的牌型
        if not last_play:
            all_moves.extend(self._generate_all_types(cards))
        else:
            # 生成能压过上家的牌
            all_moves.extend(self._generate_beat_moves(cards, last_play))

        # 添加"不出"选项
        if last_play:
            all_moves.append([])  # 空列表表示不出

        return all_moves

    def _generate_all_types(self, cards: List[Card]) -> List[List[Card]]:
        """生成所有可能的牌型"""
        moves = []

        # 单张
        for card in cards:
            moves.append([card])

        # 按牌面分组
        rank_groups = self._group_by_rank(cards)

        # 对子
        for rank, group in rank_groups.items():
            if len(group) >= 2:
                moves.append(group[:2])

        # 三张
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                moves.append(group[:3])

        # 三带一
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                triple = group[:3]
                for card in cards:
                    if card.rank != rank:
                        moves.append(triple + [card])

        # 三带二
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                triple = group[:3]
                for rank2, group2 in rank_groups.items():
                    if rank2 != rank and len(group2) >= 2:
                        moves.append(triple + group2[:2])

        # 炸弹
        for rank, group in rank_groups.items():
            if len(group) >= 4:
                moves.append(group[:4])

        # 四带二
        for rank, group in rank_groups.items():
            if len(group) >= 4:
                four = group[:4]
                # 带两个单张
                singles = [c for c in cards if c.rank != rank]
                if len(singles) >= 2:
                    for pair in combinations(singles, 2):
                        moves.append(four + list(pair))
                # 带一对
                for rank2, group2 in rank_groups.items():
                    if rank2 != rank and len(group2) >= 2:
                        moves.append(four + group2[:2])

        # 王炸
        jokers = [c for c in cards if c.is_joker]
        if len(jokers) == 2:
            moves.append(jokers)

        # 顺子
        moves.extend(self._generate_straights(cards))

        # 连对
        moves.extend(self._generate_pair_straights(cards))

        # 飞机
        moves.extend(self._generate_airplanes(cards))

        # 去重
        moves = self._deduplicate_moves(moves)

        return moves

    def _generate_beat_moves(self, cards: List[Card], last_play: List[Card]) -> List[List[Card]]:
        """生成能压过上家的牌"""
        last_result = analyze_hand(last_play)
        if not last_result.is_valid:
            return []

        moves = []

        # 王炸
        jokers = [c for c in cards if c.is_joker]
        if len(jokers) == 2:
            moves.append(jokers)

        # 炸弹(如果上家不是炸弹或王炸)
        if last_result.play_type not in ('BOMB', 'ROCKET'):
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 4:
                    moves.append(group[:4])

        # 如果上家是炸弹
        if last_result.play_type == 'BOMB':
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 4:
                    # 检查炸弹是否更大
                    bomb_value = CARD_ORDER.get(rank, 0)
                    if bomb_value > last_result.rank_value:
                        moves.append(group[:4])

        # 同牌型
        moves.extend(self._generate_same_type(cards, last_play))

        # 去重
        moves = self._deduplicate_moves(moves)

        return moves

    def _generate_same_type(self, cards: List[Card], last_play: List[Card]) -> List[List[Card]]:
        """生成同牌型的出牌"""
        last_result = analyze_hand(last_play)
        moves = []

        if last_result.play_type == 'SINGLE':
            # 单张
            for card in cards:
                if CARD_ORDER.get(card.rank, 0) > last_result.rank_value:
                    moves.append([card])

        elif last_result.play_type == 'PAIR':
            # 对子
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 2 and CARD_ORDER.get(rank, 0) > last_result.rank_value:
                    moves.append(group[:2])

        elif last_result.play_type == 'TRIPLE':
            # 三张
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 3 and CARD_ORDER.get(rank, 0) > last_result.rank_value:
                    moves.append(group[:3])

        elif last_result.play_type == 'TRIPLE_1':
            # 三带一
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 3 and CARD_ORDER.get(rank, 0) > last_result.rank_value:
                    triple = group[:3]
                    for card in cards:
                        if card.rank != rank:
                            moves.append(triple + [card])

        elif last_result.play_type == 'TRIPLE_2':
            # 三带二
            rank_groups = self._group_by_rank(cards)
            for rank, group in rank_groups.items():
                if len(group) >= 3 and CARD_ORDER.get(rank, 0) > last_result.rank_value:
                    triple = group[:3]
                    for rank2, group2 in rank_groups.items():
                        if rank2 != rank and len(group2) >= 2:
                            moves.append(triple + group2[:2])

        elif last_result.play_type == 'STRAIGHT':
            # 顺子
            straights = self._generate_straights(cards)
            for straight in straights:
                result = analyze_hand(straight)
                if result.is_valid and result.length == last_result.length and result.rank_value > last_result.rank_value:
                    moves.append(straight)

        elif last_result.play_type == 'PAIR_STRAIGHT':
            # 连对
            pair_straights = self._generate_pair_straights(cards)
            for ps in pair_straights:
                result = analyze_hand(ps)
                if result.is_valid and result.length == last_result.length and result.rank_value > last_result.rank_value:
                    moves.append(ps)

        return moves

    def _group_by_rank(self, cards: List[Card]) -> dict:
        """按牌面分组"""
        groups = {}
        for card in cards:
            if card.rank not in groups:
                groups[card.rank] = []
            groups[card.rank].append(card)
        return groups

    def _generate_straights(self, cards: List[Card]) -> List[List[Card]]:
        """生成顺子"""
        straights = []
        normal_cards = [c for c in cards if not c.is_joker and CARD_ORDER.get(c.rank, 0) <= 14]

        if len(normal_cards) < 5:
            return []

        # 找出所有不重复的牌面值
        unique_values = sorted({CARD_ORDER.get(c.rank, 0) for c in normal_cards})

        # 找连续序列
        for length in range(5, min(13, len(unique_values)) + 1):
            for i in range(len(unique_values) - length + 1):
                seq = unique_values[i:i + length]
                if seq[-1] - seq[0] == length - 1:
                    # 每张牌选一张
                    straight = []
                    for val in seq:
                        # 找这个值的牌
                        for card in normal_cards:
                            if CARD_ORDER.get(card.rank, 0) == val:
                                straight.append(card)
                                break
                    if len(straight) == length:
                        straights.append(straight)

        return straights

    def _generate_pair_straights(self, cards: List[Card]) -> List[List[Card]]:
        """生成连对"""
        pair_straights = []
        rank_groups = self._group_by_rank(cards)

        # 找出有对子的牌面
        pair_ranks = [r for r, g in rank_groups.items()
                      if len(g) >= 2 and CARD_ORDER.get(r, 0) <= 14]
        pair_ranks.sort(key=lambda r: CARD_ORDER.get(r, 0))

        if len(pair_ranks) < 3:
            return []

        # 找连续序列
        for length in range(3, len(pair_ranks) + 1):
            for i in range(len(pair_ranks) - length + 1):
                seq = pair_ranks[i:i + length]
                values = [CARD_ORDER.get(r, 0) for r in seq]
                if values[-1] - values[0] == length - 1:
                    ps = []
                    for r in seq:
                        ps.extend(rank_groups[r][:2])
                    pair_straights.append(ps)

        return pair_straights

    def _generate_airplanes(self, cards: List[Card]) -> List[List[Card]]:
        """生成飞机(简单版)"""
        airplanes = []
        rank_groups = self._group_by_rank(cards)

        # 找出有三张的牌面
        triple_ranks = [r for r, g in rank_groups.items()
                        if len(g) >= 3 and CARD_ORDER.get(r, 0) <= 14]
        triple_ranks.sort(key=lambda r: CARD_ORDER.get(r, 0))

        if len(triple_ranks) < 2:
            return []

        # 找连续序列
        for length in range(2, len(triple_ranks) + 1):
            for i in range(len(triple_ranks) - length + 1):
                seq = triple_ranks[i:i + length]
                values = [CARD_ORDER.get(r, 0) for r in seq]
                if values[-1] - values[0] == length - 1:
                    plane = []
                    for r in seq:
                        plane.extend(rank_groups[r][:3])
                    airplanes.append(plane)

        return airplanes

    def _deduplicate_moves(self, moves: List[List[Card]]) -> List[List[Card]]:
        """去重"""
        seen = set()
        unique = []
        for move in moves:
            key = tuple(sorted(c.rank for c in move))
            if key not in seen:
                seen.add(key)
                unique.append(move)
        return unique
