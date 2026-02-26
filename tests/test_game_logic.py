"""
游戏逻辑测试
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.card import Card, create_deck, sort_cards, count_card_ranks
from src.game.move_validator import analyze_hand, can_beat


def test_card_creation():
    """测试卡片创建"""
    print("Testing card creation...")
    card = Card(rank='A', suit=None)
    print(f"  Created: {card}")
    assert card.rank == 'A'

    joker_small = Card(rank='joker_small')
    print(f"  Small joker: {joker_small}")
    assert joker_small.is_joker

    print("  Passed")


def test_deck_creation():
    """测试牌组创建"""
    print("\nTesting deck creation...")
    deck = create_deck()
    print(f"  Deck size: {len(deck)}")
    assert len(deck) == 54

    # 统计牌面
    counts = count_card_ranks(deck)
    print(f"  Rank counts: 3={counts['3']}, joker_small={counts['joker_small']}")
    assert counts['3'] == 4
    assert counts['joker_small'] == 1

    print("  Passed")


def test_hand_analysis():
    """测试牌型分析"""
    print("\nTesting hand analysis...")

    # 单张
    single = [Card(rank='5')]
    result = analyze_hand(single)
    print(f"  Single: {result.play_type}, valid={result.is_valid}")
    assert result.is_valid
    assert result.play_type == 'SINGLE'

    # 对子
    pair = [Card(rank='10'), Card(rank='10')]
    result = analyze_hand(pair)
    print(f"  Pair: {result.play_type}, valid={result.is_valid}")
    assert result.is_valid
    assert result.play_type == 'PAIR'

    # 三张
    triple = [Card(rank='K'), Card(rank='K'), Card(rank='K')]
    result = analyze_hand(triple)
    print(f"  Triple: {result.play_type}, valid={result.is_valid}")
    assert result.is_valid
    assert result.play_type == 'TRIPLE'

    # 炸弹
    bomb = [Card(rank='2'), Card(rank='2'), Card(rank='2'), Card(rank='2')]
    result = analyze_hand(bomb)
    print(f"  Bomb: {result.play_type}, valid={result.is_valid}")
    assert result.is_valid
    assert result.play_type == 'BOMB'

    # 王炸
    rocket = [Card(rank='joker_small'), Card(rank='joker_big')]
    result = analyze_hand(rocket)
    print(f"  Rocket: {result.play_type}, valid={result.is_valid}")
    assert result.is_valid
    assert result.play_type == 'ROCKET'

    print("  Passed")


def test_can_beat():
    """测试压牌"""
    print("\nTesting can beat...")

    # 单张压单张
    card3 = [Card(rank='3')]
    card5 = [Card(rank='5')]
    assert can_beat(card5, card3)
    assert not can_beat(card3, card5)
    print("  Single beat: OK")

    # 炸弹压单张
    bomb = [Card(rank='9'), Card(rank='9'), Card(rank='9'), Card(rank='9')]
    assert can_beat(bomb, card5)
    print("  Bomb beat single: OK")

    # 王炸压炸弹
    rocket = [Card(rank='joker_small'), Card(rank='joker_big')]
    assert can_beat(rocket, bomb)
    print("  Rocket beat bomb: OK")

    print("  Passed")


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Game Logic Tests")
    print("=" * 50)

    try:
        test_card_creation()
        test_deck_creation()
        test_hand_analysis()
        test_can_beat()

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
