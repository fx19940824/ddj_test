"""
游戏状态管理
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import json

from config.settings import GameRegions, CONFIG_FILE, CARD_RANKS, JOKER_SMALL, JOKER_BIG
from .card import Card, sort_cards, count_card_ranks


class GamePhase(Enum):
    """游戏阶段"""
    IDLE = "idle"           # 空闲
    BIDDING = "bidding"     # 叫地主
    PLAYING = "playing"     # 出牌中
    FINISHED = "finished"   # 结束


class PlayerRole(Enum):
    """玩家角色"""
    LANDLORD = "landlord"    # 地主
    PEASANT = "peasant"      # 农民


@dataclass
class GameState:
    """游戏状态"""
    # 游戏阶段
    phase: GamePhase = GamePhase.IDLE

    # 玩家信息
    my_hand: List[Card] = field(default_factory=list)  # 我的手牌
    player1_remaining: int = 17  # 玩家1剩余牌数
    player2_remaining: int = 17  # 玩家2剩余牌数
    my_role: PlayerRole = PlayerRole.PEASANT  # 我的角色

    # 出牌记录
    played_cards: List[Card] = field(default_factory=list)  # 已出的牌
    current_play: List[Card] = field(default_factory=list)   # 当前桌上的牌
    last_play_player: Optional[int] = None  # 最后出牌的玩家

    # 游戏轮次
    current_player: int = 0  # 当前出牌玩家(0=我, 1=玩家1, 2=玩家2)
    round_count: int = 0

    # 配置
    regions: GameRegions = field(default_factory=GameRegions)

    def reset(self):
        """重置游戏状态"""
        self.phase = GamePhase.IDLE
        self.my_hand = []
        self.player1_remaining = 17
        self.player2_remaining = 17
        self.my_role = PlayerRole.PEASANT
        self.played_cards = []
        self.current_play = []
        self.last_play_player = None
        self.current_player = 0
        self.round_count = 0

    def add_my_hand(self, cards: List[Card]):
        """添加手牌"""
        for card in cards:
            if card not in self.my_hand:
                self.my_hand.append(card)
        self.my_hand = sort_cards(self.my_hand)

    def remove_my_hand(self, cards: List[Card]):
        """移除手牌(我出牌后)"""
        for card in cards:
            if card in self.my_hand:
                self.my_hand.remove(card)

    def add_played_cards(self, cards: List[Card], player: int):
        """记录已出牌"""
        self.played_cards.extend(cards)
        self.current_play = cards
        self.last_play_player = player

        # 更新剩余牌数
        if player == 1:
            self.player1_remaining -= len(cards)
        elif player == 2:
            self.player2_remaining -= len(cards)

    def get_remaining_card_counts(self) -> Dict[str, int]:
        """
        获取对手剩余牌统计

        Returns:
            {牌面: 数量}
        """
        # 所有牌
        all_ranks = CARD_RANKS + [JOKER_SMALL, JOKER_BIG]

        # 统计已出的牌
        played_count = count_card_ranks(self.played_cards)

        # 统计我手里的牌
        my_count = count_card_ranks(self.my_hand)

        # 计算剩余的牌 = 总数(4) - 已出 - 我手里的
        remaining = {}
        for rank in all_ranks:
            total = 4 if rank not in (JOKER_SMALL, JOKER_BIG) else 1
            played = played_count.get(rank, 0)
            my = my_count.get(rank, 0)
            rem = total - played - my
            if rem > 0:
                remaining[rank] = rem

        return remaining

    def is_my_turn(self) -> bool:
        """是否轮到我出牌"""
        return self.current_player == 0 and self.phase == GamePhase.PLAYING

    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'hand_region': self.regions.hand_region,
            'play_region': self.regions.play_region,
            'player1_count': self.regions.player1_count,
            'player2_count': self.regions.player2_count,
            'landlord_indicator': self.regions.landlord_indicator,
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    def load_config(self):
        """从文件加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.regions.hand_region = tuple(config_data.get('hand_region')) if config_data.get('hand_region') else None
                self.regions.play_region = tuple(config_data.get('play_region')) if config_data.get('play_region') else None
                self.regions.player1_count = tuple(config_data.get('player1_count')) if config_data.get('player1_count') else None
                self.regions.player2_count = tuple(config_data.get('player2_count')) if config_data.get('player2_count') else None
                self.regions.landlord_indicator = tuple(config_data.get('landlord_indicator')) if config_data.get('landlord_indicator') else None
            except Exception:
                pass
