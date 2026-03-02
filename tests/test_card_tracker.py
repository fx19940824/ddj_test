"""
牌张跟踪器测试
测试 CardTracker 类和剩余牌统计功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.game.card import Card


def test_card_tracker():
    """测试牌张跟踪器"""
    print("Testing CardTracker and remaining cards...")

    state = GameState()
    tracker = CardTracker(state)

    # 添加手牌
    state.my_hand = [
        Card(rank='3'),
        Card(rank='5'),
        Card(rank='A'),
    ]

    # 添加已出牌
    state.played_cards = [
        Card(rank='3'),
        Card(rank='3'),
    ]

    # 测试剩余牌统计
    remaining = state.get_remaining_card_counts()
    # 3 总共有4张，我手里1张，已出2张，应该剩余1张
    assert remaining.get('3') == 1, f"Expected 1 '3' remaining, got {remaining.get('3')}"
    # 5 总共有4张，我手里1张，已出0张，应该剩余3张
    assert remaining.get('5') == 3, f"Expected 3 '5' remaining, got {remaining.get('5')}"
    # A 总共有4张，我手里1张，已出0张，应该剩余3张
    assert remaining.get('A') == 3, f"Expected 3 'A' remaining, got {remaining.get('A')}"
    print("  [OK] Remaining cards calculation works")


def test_joker_remaining():
    """测试王牌剩余统计"""
    print("\nTesting joker remaining...")

    state = GameState()

    # 添加小王到手牌
    state.my_hand = [Card(rank='joker_small')]

    # 没有已出的牌
    state.played_cards = []

    remaining = state.get_remaining_card_counts()
    # 小王总共有1张，我手里1张，应该剩余0张（不在remaining里）
    assert 'joker_small' not in remaining, "joker_small should not be in remaining"
    # 大王总共有1张，不在手里也没出，应该剩余1张
    assert remaining.get('joker_big') == 1, f"Expected 1 joker_big remaining, got {remaining.get('joker_big')}"
    print("  [OK] Joker remaining works")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Card Tracker Tests")
    print("=" * 60)

    try:
        test_card_tracker()
        test_joker_remaining()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
