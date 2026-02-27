"""
测试核心功能（不依赖GUI）
"""
from src.game.card import Card, sort_cards, cards_to_str
from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.ai.optimal_play import OptimalPlayEngine


def demo():
    """演示核心功能"""
    print("=" * 60)
    print("欢乐斗地主辅助 - 核心功能演示")
    print("=" * 60)

    # 1. 创建游戏状态
    print("\n1. 初始化游戏状态...")
    game_state = GameState()
    card_tracker = CardTracker(game_state)
    ai_engine = OptimalPlayEngine()

    # 2. 输入手牌
    print("\n2. 输入手牌...")
    my_hand = [
        Card(rank='3'), Card(rank='4'), Card(rank='5'),
        Card(rank='6'), Card(rank='7'),
        Card(rank='9'), Card(rank='9'),
        Card(rank='J'), Card(rank='J'), Card(rank='J'),
        Card(rank='A'), Card(rank='A'),
        Card(rank='2'),
    ]
    game_state.my_hand = sort_cards(my_hand)
    print(f"   我的手牌: {cards_to_str(my_hand)}")

    # 3. 记录一些已出牌
    print("\n3. 记录已出牌...")
    played_cards = [
        Card(rank='3'), Card(rank='3'),
        Card(rank='10'), Card(rank='10'),
        Card(rank='K'),
    ]
    game_state.played_cards = played_cards
    print(f"   已出牌: {cards_to_str(played_cards)}")

    # 4. 显示剩余牌统计
    print("\n4. 对手剩余牌统计:")
    remaining = card_tracker.get_remaining_display()
    for line in remaining:
        print(f"   {line}")

    # 5. 生成出牌建议（首次出牌）
    print("\n5. 首次出牌 - AI推荐:")
    suggestions = ai_engine.get_suggestions(my_hand, last_play=None, game_state=game_state)
    for i, s in enumerate(suggestions):
        prefix = "★首选" if i == 0 else f"方案{i+1}"
        print(f"   [{prefix}] {s}")

    # 6. 模拟上家出牌
    print("\n6. 上家出牌: 单张 10")
    last_play = [Card(rank='10')]
    game_state.current_play = last_play

    # 7. 生成压牌建议
    print("\n7. 压牌建议 - AI推荐:")
    suggestions = ai_engine.get_suggestions(my_hand, last_play=last_play, game_state=game_state)
    for i, s in enumerate(suggestions):
        prefix = "★首选" if i == 0 else f"方案{i+1}"
        print(f"   [{prefix}] {s}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo()
