"""
AI模块测试
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.card import Card
from src.ai.optimal_play import OptimalPlayEngine
from src.ai.move_generator import MoveGenerator
from src.ai.hand_evaluator import HandEvaluator


def test_hand_analysis():
    """测试手牌分析"""
    print("Testing hand analysis...")

    evaluator = HandEvaluator()

    # 创建测试手牌
    cards = [
        Card(rank='3'), Card(rank='4'), Card(rank='5'),
        Card(rank='6'), Card(rank='7'),
        Card(rank='9'), Card(rank='9'),
        Card(rank='J'), Card(rank='J'), Card(rank='J'),
    ]

    analysis = evaluator.analyze_hand_combinations(cards)
    print(f"  Singles: {len(analysis.single_cards)}")
    print(f"  Pairs: {len(analysis.pairs)}")
    print(f"  Triples: {len(analysis.triples)}")
    print(f"  Straights: {len(analysis.straights)}")

    print("  Passed")


def test_move_generation():
    """测试出牌生成"""
    print("\nTesting move generation...")

    generator = MoveGenerator()

    # 简单手牌
    cards = [
        Card(rank='3'), Card(rank='3'),
        Card(rank='5'),
        Card(rank='10'), Card(rank='10'), Card(rank='10'),
    ]

    moves = generator.generate_all_moves(cards, last_play=None)
    print(f"  Generated {len(moves)} possible moves")

    # 测试压牌
    last_play = [Card(rank='5')]
    beat_moves = generator.generate_all_moves(cards, last_play)
    print(f"  Generated {len(beat_moves)} beat moves")

    print("  Passed")


def test_optimal_play():
    """测试最优出牌"""
    print("\nTesting optimal play...")

    engine = OptimalPlayEngine()

    # 测试手牌
    my_hand = [
        Card(rank='3'), Card(rank='4'), Card(rank='5'),
        Card(rank='6'), Card(rank='7'),
        Card(rank='9'), Card(rank='9'),
        Card(rank='A'), Card(rank='A'), Card(rank='A'),
        Card(rank='2'),
    ]

    # 首次出牌
    suggestions = engine.get_suggestions(my_hand, last_play=None)
    print(f"  Suggestions: {len(suggestions)}")
    for i, s in enumerate(suggestions):
        print(f"    {i+1}. {s}")

    # 有上家出牌
    last_play = [Card(rank='10')]
    suggestions = engine.get_suggestions(my_hand, last_play=last_play)
    print(f"\n  Last play: single 10, suggestions: {len(suggestions)}")
    for i, s in enumerate(suggestions):
        print(f"    {i+1}. {s}")

    print("  Passed")


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("AI Module Tests")
    print("=" * 50)

    try:
        test_hand_analysis()
        test_move_generation()
        test_optimal_play()

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
