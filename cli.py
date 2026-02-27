"""
命令行版本 - 欢乐斗地主辅助
不需要PyQt6，直接在控制台使用
"""
from src.game.card import Card, sort_cards, cards_to_str
from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.ai.optimal_play import OptimalPlayEngine


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def input_cards(prompt):
    """输入多张牌"""
    print(f"\n{prompt}")
    print("输入格式: 牌面数量, 用空格分隔")
    print("例如: 3 4 5 6 7 9 9 J J J A A 2")
    print("王牌: joker_small joker_big")
    print("输入空行结束")

    cards = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        for rank in line.split():
            if rank:
                rank = rank.upper()
                if rank in ('11', 'J'):
                    rank = 'J'
                elif rank in ('12', 'Q'):
                    rank = 'Q'
                elif rank in ('13', 'K'):
                    rank = 'K'
                elif rank in ('14', '1', 'A'):
                    rank = 'A'
                elif rank in ('15', '2'):
                    rank = '2'
                elif rank in ('S', 'X', 'SJ', '小王'):
                    rank = 'joker_small'
                elif rank in ('B', 'BJ', '大王'):
                    rank = 'joker_big'
                cards.append(Card(rank=rank))

    return sort_cards(cards)


def main():
    """主函数"""
    print_header("欢乐斗地主辅助 - 命令行版")

    # 初始化
    game_state = GameState()
    card_tracker = CardTracker(game_state)
    ai_engine = OptimalPlayEngine()

    # 输入手牌
    print_header("第一步: 输入我的手牌")
    game_state.my_hand = input_cards("请输入我的手牌（输入空行结束）:")
    if not game_state.my_hand:
        print("未输入手牌，退出")
        return

    print(f"\n我的手牌: {cards_to_str(game_state.my_hand)}")

    # 主循环
    while True:
        print_header("当前状态")

        # 显示剩余牌
        print("\n对手剩余牌统计:")
        remaining = card_tracker.get_remaining_display()
        for line in remaining:
            print(f"  {line}")

        # 显示AI建议
        print(f"\n我的手牌: {cards_to_str(game_state.my_hand)}")

        print("\nAI推荐出牌:")
        suggestions = ai_engine.get_suggestions(
            game_state.my_hand,
            game_state.current_play,
            game_state
        )
        for i, s in enumerate(suggestions):
            prefix = "★首选" if i == 0 else f"方案{i+1}"
            print(f"  [{prefix}] {s}")

        # 操作菜单
        print_header("操作菜单")
        print("1. 我出牌了")
        print("2. 记录其他玩家出牌")
        print("3. 设置上家出牌（用于压牌建议）")
        print("4. 查看剩余牌")
        print("5. 重置本局")
        print("0. 退出")

        choice = input("\n请选择操作 (0-5): ").strip()

        if choice == '1':
            # 我出牌了
            print_header("我出牌了")
            played = input_cards("请输入我出的牌:")
            if played:
                # 从手牌中移除
                for card in played:
                    if card in game_state.my_hand:
                        game_state.my_hand.remove(card)
                # 记录已出牌
                game_state.played_cards.extend(played)
                game_state.current_play = played
                print(f"已出牌: {cards_to_str(played)}")
                if not game_state.my_hand:
                    print("\n恭喜！手牌出完了！")
                    break

        elif choice == '2':
            # 记录其他玩家出牌
            print_header("记录其他玩家出牌")
            played = input_cards("请输入其他玩家出的牌:")
            if played:
                game_state.played_cards.extend(played)
                print(f"已记录: {cards_to_str(played)}")

        elif choice == '3':
            # 设置上家出牌
            print_header("设置上家出牌")
            played = input_cards("请输入上家出的牌:")
            game_state.current_play = played
            if played:
                print(f"上家出牌: {cards_to_str(played)}")
            else:
                print("已清除上家出牌")

        elif choice == '4':
            # 查看剩余牌，已在上面显示
            pass

        elif choice == '5':
            # 重置
            confirm = input("确定要重置吗？(y/n): ").strip().lower()
            if confirm == 'y':
                game_state.reset()
                card_tracker.reset()
                print_header("重新开始")
                game_state.my_hand = input_cards("请输入我的手牌:")
                if not game_state.my_hand:
                    print("未输入手牌，退出")
                    return

        elif choice == '0':
            # 退出
            print("再见！")
            break

        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n再见！")
