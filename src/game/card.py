"""
卡片类定义
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from config.settings import (
    CARD_RANKS,
    CARD_SUITS,
    CARD_SUITS_SIMPLE,
    JOKER_SMALL,
    JOKER_BIG,
    CARD_ORDER,
)


class Suit(Enum):
    """花色枚举"""
    SPADE = 'S'
    HEART = 'H'
    CLUB = 'C'
    DIAMOND = 'D'


@dataclass
class Card:
    """卡片类"""
    rank: str  # 牌面: '3'-'10', 'J', 'Q', 'K', 'A', '2', 'joker_small', 'joker_big'
    suit: Optional[Suit] = None  # 花色(小王大王没有花色)

    def __post_init__(self):
        # 验证牌面有效性
        valid_ranks = CARD_RANKS + [JOKER_SMALL, JOKER_BIG]
        if self.rank not in valid_ranks:
            raise ValueError(f"Invalid rank: {self.rank}")

        # 王牌不需要花色
        if self.is_joker:
            self.suit = None
        elif self.suit is None:
            # 默认给黑桃
            self.suit = Suit.SPADE

    @property
    def is_joker(self) -> bool:
        """是否是王牌"""
        return self.rank in (JOKER_SMALL, JOKER_BIG)

    @property
    def is_small_joker(self) -> bool:
        """是否是小王"""
        return self.rank == JOKER_SMALL

    @property
    def is_big_joker(self) -> bool:
        """是否是大王"""
        return self.rank == JOKER_BIG

    @property
    def order_value(self) -> int:
        """获取牌面大小值(用于比较)"""
        return CARD_ORDER.get(self.rank, 0)

    def __str__(self) -> str:
        if self.is_small_joker:
            return "joker_small"
        if self.is_big_joker:
            return "joker_big"
        return f"{self.rank}"

    def __repr__(self) -> str:
        return f"Card('{self.rank}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other) -> bool:
        """小于比较(按牌面大小)"""
        if not isinstance(other, Card):
            return NotImplemented
        return self.order_value < other.order_value

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'rank': self.rank,
            'suit': self.suit.value if self.suit else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """从字典创建"""
        suit = Suit(data['suit']) if data.get('suit') else None
        return cls(rank=data['rank'], suit=suit)


def create_deck(include_jokers: bool = True) -> List[Card]:
    """
    创建一副牌

    Args:
        include_jokers: 是否包含大小王

    Returns:
        卡片列表
    """
    deck = []

    # 创建普通牌
    for rank in CARD_RANKS:
        for suit in Suit:
            deck.append(Card(rank=rank, suit=suit))

    # 添加王牌
    if include_jokers:
        deck.append(Card(rank=JOKER_SMALL))
        deck.append(Card(rank=JOKER_BIG))

    return deck


def sort_cards(cards: List[Card], reverse: bool = False) -> List[Card]:
    """
    排序卡片

    Args:
        cards: 卡片列表
        reverse: 是否降序

    Returns:
        排序后的卡片列表
    """
    return sorted(cards, key=lambda c: c.order_value, reverse=reverse)


def cards_to_str(cards: List[Card]) -> str:
    """
    卡片列表转字符串

    Args:
        cards: 卡片列表

    Returns:
        字符串表示
    """
    return " ".join(str(card) for card in sort_cards(cards))


def count_card_ranks(cards: List[Card]) -> dict:
    """
    统计每种牌面的数量

    Args:
        cards: 卡片列表

    Returns:
        {牌面: 数量}
    """
    count = {}
    for card in cards:
        rank = card.rank
        count[rank] = count.get(rank, 0) + 1
    return count
