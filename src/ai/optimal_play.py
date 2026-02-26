"""
最优出牌算法
"""
from typing import List, Optional
from dataclasses import dataclass

from src.game.card import Card, sort_cards, cards_to_str
from src.game.move_validator import (
    analyze_hand,
    PlayResult,
    can_beat,
)
from src.game.game_state import GameState, PlayerRole
from .move_generator import MoveGenerator
from .hand_evaluator import HandEvaluator


@dataclass
class PlaySuggestion:
    """出牌建议"""
    cards: List[Card]
    play_type: str
    rank_value: int
    score: float
    reason: str
    is_pass: bool = False

    def __str__(self) -> str:
        if self.is_pass:
            return "不出"
        type_name = {
            'SINGLE': '单张', 'PAIR': '对子', 'TRIPLE': '三张',
            'TRIPLE_1': '三带一', 'TRIPLE_2': '三带二',
            'STRAIGHT': '顺子', 'PAIR_STRAIGHT': '连对',
            'AIRPLANE': '飞机', 'AIRPLANE_1': '飞机带单',
            'AIRPLANE_2': '飞机带对', 'FOUR_2': '四带二',
            'BOMB': '炸弹', 'ROCKET': '王炸',
        }
        return f"{type_name.get(self.play_type, '未知')}: {cards_to_str(self.cards)}"


class OptimalPlayEngine:
    """最优出牌引擎"""

    def __init__(self):
        self.move_generator = MoveGenerator()
        self.hand_evaluator = HandEvaluator()

    def get_suggestions(self,
                       my_hand: List[Card],
                       last_play: Optional[List[Card]] = None,
                       game_state: Optional[GameState] = None) -> List[PlaySuggestion]:
        """
        获取出牌建议

        Args:
            my_hand: 我的手牌
            last_play: 上家出的牌
            game_state: 游戏状态

        Returns:
            出牌建议列表(按优先级排序)
        """
        if not my_hand:
            return []

        # 生成所有合法出牌
        all_moves = self.move_generator.generate_all_moves(my_hand, last_play)

        if not all_moves:
            return [PlaySuggestion(
                cards=[],
                play_type='',
                rank_value=0,
                score=0,
                reason='无牌可出',
                is_pass=True
            )]

        # 评估每个出牌
        suggestions = []
        for move in all_moves:
            if not move:
                # 不出
                suggestions.append(PlaySuggestion(
                    cards=[],
                    play_type='PASS',
                    rank_value=0,
                    score=-10,
                    reason='选择不出',
                    is_pass=True
                ))
            else:
                result = analyze_hand(move)
                if result.is_valid:
                    score = self._score_move(move, my_hand, last_play, game_state, result)
                    suggestions.append(PlaySuggestion(
                        cards=move,
                        play_type=result.play_type,
                        rank_value=result.rank_value,
                        score=score,
                        reason=self._explain_score(move, result, score)
                    ))

        # 按分数排序
        suggestions.sort(key=lambda s: s.score, reverse=True)

        # 返回前3个建议
        return suggestions[:3]

    def _score_move(self,
                   move: List[Card],
                   my_hand: List[Card],
                   last_play: Optional[List[Card]],
                   game_state: Optional[GameState],
                   result: PlayResult) -> float:
        """
        为出牌打分

        Args:
            move: 出牌
            my_hand: 手牌
            last_play: 上家出牌
            game_state: 游戏状态
            result: 出牌分析结果

        Returns:
            分数(越高越好)
        """
        score = 0.0

        # 获取角色
        is_landlord = False
        if game_state:
            is_landlord = game_state.my_role == PlayerRole.LANDLORD

        # 剩余手牌
        remaining_hand = [c for c in my_hand if c not in move]

        # 1. 能出牌就比不出好
        score += 10

        # 2. 牌型策略
        play_type = result.play_type

        # 王炸 - 留到关键时刻
        if play_type == 'ROCKET':
            if len(my_hand) <= 4:
                score += 100  # 最后几张可以出
            else:
                score -= 50  # 不要轻易出

        # 炸弹
        elif play_type == 'BOMB':
            if len(my_hand) <= 6:
                score += 50  # 快出完了可以炸
            elif last_play and len(last_play) >= 4:
                score += 40  # 拆炸弹
            else:
                score -= 30  # 保留炸弹

        # 顺子/连对 - 鼓励出
        elif play_type in ('STRAIGHT', 'PAIR_STRAIGHT'):
            score += 30
            # 顺子越长越好
            score += len(move) * 2

        # 三带一/三带二 - 可以出掉小牌
        elif play_type in ('TRIPLE_1', 'TRIPLE_2'):
            score += 20

        # 对子
        elif play_type == 'PAIR':
            # 小对子可以出
            if result.rank_value <= 10:
                score += 15
            else:
                score += 5

        # 单张
        elif play_type == 'SINGLE':
            # 出小单张
            if result.rank_value <= 10:
                score += 10
            elif result.rank_value >= 14:  # A, 2
                score -= 5  # 大牌尽量留

        # 3. 评估剩余手牌
        remaining_strength = self.hand_evaluator.evaluate_hand_strength(remaining_hand)
        score += remaining_strength * 0.5

        # 4. 如果是地主, 更积极出牌
        if is_landlord:
            score += 10

        # 5. 能赢的牌
        if len(remaining_hand) == 0:
            score += 1000  # 必胜

        return score

    def _explain_score(self, move: List[Card], result: PlayResult, score: float) -> str:
        """解释打分原因"""
        if score >= 1000:
            return "必胜！"
        if score >= 50:
            return "推荐出这手牌"
        if score >= 20:
            return "可以出这手牌"
        if score >= 0:
            return "一般选择"
        return "谨慎选择"

    def get_best_suggestion(self,
                           my_hand: List[Card],
                           last_play: Optional[List[Card]] = None,
                           game_state: Optional[GameState] = None) -> Optional[PlaySuggestion]:
        """
        获取最佳出牌建议

        Args:
            my_hand: 我的手牌
            last_play: 上家出的牌
            game_state: 游戏状态

        Returns:
            最佳建议
        """
        suggestions = self.get_suggestions(my_hand, last_play, game_state)
        return suggestions[0] if suggestions else None
