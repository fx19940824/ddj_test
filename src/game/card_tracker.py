"""
记牌器逻辑
"""
from typing import List, Dict, Optional
from collections import Counter

from .card import Card, count_card_ranks
from .game_state import GameState
from config.settings import CARD_RANKS, JOKER_SMALL, JOKER_BIG


class CardTracker:
    """记牌器"""

    def __init__(self, game_state: GameState):
        self.game_state = game_state

        # 完整牌组统计
        self.full_deck_count = self._init_full_deck()

    def _init_full_deck(self) -> Dict[str, int]:
        """初始化完整牌组统计"""
        count = {}
        for rank in CARD_RANKS:
            count[rank] = 4
        count[JOKER_SMALL] = 1
        count[JOKER_BIG] = 1
        return count

    def update_from_played(self, played_cards: List[Card]):
        """从已出牌更新"""
        self.game_state.played_cards.extend(played_cards)

    def get_opponent_remaining(self) -> Dict[str, int]:
        """
        获取对手剩余牌统计

        Returns:
            {牌面: 数量}
        """
        # 统计已出的牌
        played_count = count_card_ranks(self.game_state.played_cards)

        # 统计我手里的牌
        my_count = count_card_ranks(self.game_state.my_hand)

        # 计算剩余的牌 = 总数 - 已出 - 我手里的
        remaining = {}
        for rank in self.full_deck_count:
            total = self.full_deck_count[rank]
            played = played_count.get(rank, 0)
            my = my_count.get(rank, 0)
            rem = total - played - my
            if rem > 0:
                remaining[rank] = rem

        return remaining

    def get_remaining_display(self) -> List[str]:
        """
        获取剩余牌的显示列表(用于GUI)

        Returns:
            字符串列表, 如 ["3: 2张", "4: 1张", ...]
        """
        remaining = self.get_opponent_remaining()
        display = []

        # 按牌面顺序排列
        rank_order = CARD_RANKS + [JOKER_SMALL, JOKER_BIG]

        for rank in rank_order:
            if rank in remaining:
                count = remaining[rank]
                if rank == JOKER_SMALL:
                    display_name = "小王"
                elif rank == JOKER_BIG:
                    display_name = "大王"
                else:
                    display_name = rank
                display.append(f"{display_name}: {count}张")

        return display

    def get_bombs_remaining(self) -> List[str]:
        """
        获取可能剩余的炸弹

        Returns:
            可能的炸弹牌面列表
        """
        remaining = self.get_opponent_remaining()
        bombs = []

        for rank in CARD_RANKS:
            if remaining.get(rank, 0) == 4:
                bombs.append(rank)

        # 检查王炸
        if remaining.get(JOKER_SMALL, 0) == 1 and remaining.get(JOKER_BIG, 0) == 1:
            bombs.append("王炸")

        return bombs

    def reset(self):
        """重置记牌器"""
        self.game_state.played_cards = []
