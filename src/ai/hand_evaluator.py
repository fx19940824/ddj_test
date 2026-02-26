"""
手牌评估
"""
from typing import List, Optional, Tuple, Dict
from collections import Counter
from dataclasses import dataclass

from src.game.card import Card, sort_cards, count_card_ranks
from src.game.move_validator import (
    analyze_hand,
    PlayResult,
    PLAY_TYPES,
    CARD_ORDER,
)


@dataclass
class HandAnalysis:
    """手牌分析结果"""
    single_cards: List[Card]
    pairs: List[List[Card]]
    triples: List[List[Card]]
    quads: List[List[Card]]
    straights: List[List[Card]]
    pair_straights: List[List[Card]]
    jokers: List[Card]


class HandEvaluator:
    """手牌评估器"""

    def __init__(self):
        pass

    def analyze_hand_combinations(self, cards: List[Card]) -> HandAnalysis:
        """
        分析手牌组合

        Args:
            cards: 手牌列表

        Returns:
            HandAnalysis
        """
        cards = sort_cards(cards)

        # 按牌面统计
        rank_counts = count_card_ranks(cards)
        cards_by_rank: Dict[str, List[Card]] = {}
        for card in cards:
            if card.rank not in cards_by_rank:
                cards_by_rank[card.rank] = []
            cards_by_rank[card.rank].append(card)

        # 分离王牌
        jokers = [c for c in cards if c.is_joker]
        normal_cards = [c for c in cards if not c.is_joker]

        single_cards = []
        pairs = []
        triples = []
        quads = []

        # 分类单张、对子、三张、炸弹
        for rank, cards_list in cards_by_rank.items():
            if rank in ('joker_small', 'joker_big'):
                continue
            count = len(cards_list)
            if count == 1:
                single_cards.extend(cards_list)
            elif count == 2:
                pairs.append(cards_list)
            elif count == 3:
                triples.append(cards_list)
            elif count == 4:
                quads.append(cards_list)

        # 找顺子
        straights = self._find_straights(normal_cards)

        # 找连对
        pair_straights = self._find_pair_straights(normal_cards)

        return HandAnalysis(
            single_cards=single_cards,
            pairs=pairs,
            triples=triples,
            quads=quads,
            straights=straights,
            pair_straights=pair_straights,
            jokers=jokers,
        )

    def _find_straights(self, cards: List[Card]) -> List[List[Card]]:
        """找顺子"""
        if len(cards) < 5:
            return []

        straights = []
        normal_ranks = [c for c in cards if CARD_ORDER.get(c.rank, 0) <= 14]
        if not normal_ranks:
            return []

        # 按牌面值分组
        value_groups: Dict[int, List[Card]] = {}
        for card in normal_ranks:
            val = CARD_ORDER.get(card.rank, 0)
            if val not in value_groups:
                value_groups[val] = []
            value_groups[val].append(card)

        sorted_values = sorted(value_groups.keys())

        # 找连续序列
        for i in range(len(sorted_values)):
            for length in range(5, len(sorted_values) - i + 1):
                sequence = sorted_values[i:i + length]
                if sequence[-1] - sequence[0] == length - 1:
                    # 构建顺子
                    straight = []
                    for val in sequence:
                        if value_groups[val]:
                            straight.append(value_groups[val][0])
                    if len(straight) >= 5:
                        straights.append(straight)

        return straights

    def _find_pair_straights(self, cards: List[Card]) -> List[List[Card]]:
        """找连对"""
        if len(cards) < 6:
            return []

        pair_straights = []
        rank_counts = count_card_ranks(cards)

        # 找出所有对子的牌面
        pair_ranks = [r for r, cnt in rank_counts.items()
                      if cnt >= 2 and CARD_ORDER.get(r, 0) <= 14]
        pair_ranks.sort(key=lambda r: CARD_ORDER.get(r, 0))

        if len(pair_ranks) < 3:
            return []

        # 找连续序列
        for i in range(len(pair_ranks)):
            for length in range(3, len(pair_ranks) - i + 1):
                sequence = pair_ranks[i:i + length]
                values = [CARD_ORDER.get(r, 0) for r in sequence]
                if values[-1] - values[0] == length - 1:
                    # 构建连对
                    pair_straight = []
                    for r in sequence:
                        pair = [c for c in cards if c.rank == r][:2]
                        pair_straight.extend(pair)
                    if len(pair_straight) >= 6:
                        pair_straights.append(pair_straight)

        return pair_straights

    def evaluate_hand_strength(self, cards: List[Card]) -> float:
        """
        评估手牌强度

        Args:
            cards: 手牌

        Returns:
            强度分数(0-100)
        """
        if not cards:
            return 0

        analysis = self.analyze_hand_combinations(cards)
        score = 0

        # 炸弹加分
        score += len(analysis.quads) * 20

        # 王炸加分
        if len(analysis.jokers) == 2:
            score += 25

        # 三张加分
        score += len(analysis.triples) * 5

        # 对子加分
        score += len(analysis.pairs) * 2

        # 顺子加分
        score += len(analysis.straights) * 8

        # 连对加分
        score += len(analysis.pair_straights) * 10

        # 大牌加分
        big_cards = ['A', '2', 'joker_small', 'joker_big']
        for card in cards:
            if card.rank in big_cards:
                score += 3

        return min(100, score)

    def get_play_type_name(self, play_type: str) -> str:
        """获取牌型名称"""
        return PLAY_TYPES.get(play_type, '未知')
