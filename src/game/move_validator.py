"""
斗地主出牌规则验证
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import Counter

from .card import Card, sort_cards, count_card_ranks
from config.settings import (
    CARD_ORDER,
    JOKER_SMALL,
    JOKER_BIG,
    PLAY_TYPES,
)


@dataclass
class PlayResult:
    """出牌验证结果"""
    is_valid: bool
    play_type: Optional[str] = None
    rank_value: Optional[int] = None  # 牌面值(用于比较大小)
    length: int = 0  # 牌型长度(顺子长度等)
    error_msg: Optional[str] = None


def get_rank_value(card: Card) -> int:
    """获取牌面值"""
    return CARD_ORDER.get(card.rank, 0)


def analyze_hand(cards: List[Card]) -> PlayResult:
    """
    分析手牌类型

    Args:
        cards: 出牌列表

    Returns:
        PlayResult
    """
    if not cards:
        return PlayResult(is_valid=False, error_msg="空牌")

    cards = sort_cards(cards)
    n = len(cards)

    # 王炸
    if n == 2:
        ranks = {c.rank for c in cards}
        if JOKER_SMALL in ranks and JOKER_BIG in ranks:
            return PlayResult(
                is_valid=True,
                play_type='ROCKET',
                rank_value=100,
                length=2
            )

    # 按牌面统计
    rank_counts = Counter(c.rank for c in cards)
    count_values = list(rank_counts.values())
    unique_ranks = sorted(rank_counts.keys(), key=lambda r: CARD_ORDER.get(r, 0))

    # 炸弹
    if n == 4 and len(set(count_values)) == 1 and count_values[0] == 4:
        return PlayResult(
            is_valid=True,
            play_type='BOMB',
            rank_value=CARD_ORDER.get(unique_ranks[0], 0),
            length=4
        )

    # 单张
    if n == 1:
        return PlayResult(
            is_valid=True,
            play_type='SINGLE',
            rank_value=CARD_ORDER.get(cards[0].rank, 0),
            length=1
        )

    # 对子
    if n == 2 and len(set(count_values)) == 1 and count_values[0] == 2:
        return PlayResult(
            is_valid=True,
            play_type='PAIR',
            rank_value=CARD_ORDER.get(unique_ranks[0], 0),
            length=2
        )

    # 三张
    if n == 3 and len(set(count_values)) == 1 and count_values[0] == 3:
        return PlayResult(
            is_valid=True,
            play_type='TRIPLE',
            rank_value=CARD_ORDER.get(unique_ranks[0], 0),
            length=3
        )

    # 三带一
    if n == 4 and set(count_values) == {3, 1}:
        triple_rank = [r for r, cnt in rank_counts.items() if cnt == 3][0]
        return PlayResult(
            is_valid=True,
            play_type='TRIPLE_1',
            rank_value=CARD_ORDER.get(triple_rank, 0),
            length=4
        )

    # 三带二
    if n == 5 and set(count_values) == {3, 2}:
        triple_rank = [r for r, cnt in rank_counts.items() if cnt == 3][0]
        return PlayResult(
            is_valid=True,
            play_type='TRIPLE_2',
            rank_value=CARD_ORDER.get(triple_rank, 0),
            length=5
        )

    # 顺子
    if n >= 5 and len(set(count_values)) == 1 and count_values[0] == 1:
        # 检查是否连续, 且不包含2和王
        values = [CARD_ORDER.get(r, 0) for r in unique_ranks]
        if max(values) <= 14 and (max(values) - min(values) == n - 1):
            return PlayResult(
                is_valid=True,
                play_type='STRAIGHT',
                rank_value=CARD_ORDER.get(unique_ranks[-1], 0),
                length=n
            )

    # 连对
    if n >= 6 and n % 2 == 0 and set(count_values) == {2}:
        pair_count = n // 2
        values = [CARD_ORDER.get(r, 0) for r in unique_ranks]
        if max(values) <= 14 and (max(values) - min(values) == pair_count - 1):
            return PlayResult(
                is_valid=True,
                play_type='PAIR_STRAIGHT',
                rank_value=CARD_ORDER.get(unique_ranks[-1], 0),
                length=n
            )

    # 飞机 (两个连续三张)
    if n >= 6 and n % 3 == 0 and set(count_values) == {3}:
        plane_count = n // 3
        values = [CARD_ORDER.get(r, 0) for r in unique_ranks]
        if max(values) <= 14 and (max(values) - min(values) == plane_count - 1):
            return PlayResult(
                is_valid=True,
                play_type='AIRPLANE',
                rank_value=CARD_ORDER.get(unique_ranks[-1], 0),
                length=n
            )

    # 飞机带单
    if n >= 8 and n % 4 == 0:
        plane_count = n // 4
        if sorted(count_values) == ([1] * plane_count) + ([3] * plane_count):
            triple_ranks = [r for r, cnt in rank_counts.items() if cnt == 3]
            triple_ranks_sorted = sorted(triple_ranks, key=lambda r: CARD_ORDER.get(r, 0))
            values = [CARD_ORDER.get(r, 0) for r in triple_ranks_sorted]
            if len(values) >= 2 and max(values) <= 14 and (max(values) - min(values) == len(values) - 1):
                return PlayResult(
                    is_valid=True,
                    play_type='AIRPLANE_1',
                    rank_value=CARD_ORDER.get(triple_ranks_sorted[-1], 0),
                    length=n
                )

    # 飞机带对
    if n >= 10 and n % 5 == 0:
        plane_count = n // 5
        if sorted(count_values) == ([2] * plane_count) + ([3] * plane_count):
            triple_ranks = [r for r, cnt in rank_counts.items() if cnt == 3]
            triple_ranks_sorted = sorted(triple_ranks, key=lambda r: CARD_ORDER.get(r, 0))
            values = [CARD_ORDER.get(r, 0) for r in triple_ranks_sorted]
            if len(values) >= 2 and max(values) <= 14 and (max(values) - min(values) == len(values) - 1):
                return PlayResult(
                    is_valid=True,
                    play_type='AIRPLANE_2',
                    rank_value=CARD_ORDER.get(triple_ranks_sorted[-1], 0),
                    length=n
                )

    # 四带二
    if n == 6 and set(count_values) in [{4, 1, 1}, {4, 2}]:
        four_rank = [r for r, cnt in rank_counts.items() if cnt == 4][0]
        return PlayResult(
            is_valid=True,
            play_type='FOUR_2',
            rank_value=CARD_ORDER.get(four_rank, 0),
            length=6
        )

    return PlayResult(is_valid=False, error_msg="无效牌型")


def can_beat(cards: List[Card], last_play: List[Card]) -> bool:
    """
    判断出牌是否能压过上家

    Args:
        cards: 我的出牌
        last_play: 上家出的牌

    Returns:
        是否能压过
    """
    if not last_play:
        return True

    my_result = analyze_hand(cards)
    last_result = analyze_hand(last_play)

    if not my_result.is_valid:
        return False

    # 王炸最大
    if my_result.play_type == 'ROCKET':
        return True

    # 炸弹可以压非炸弹
    if my_result.play_type == 'BOMB' and last_result.play_type not in ('BOMB', 'ROCKET'):
        return True

    # 同牌型比较
    if my_result.play_type == last_result.play_type and my_result.length == last_result.length:
        return my_result.rank_value > last_result.rank_value

    return False
