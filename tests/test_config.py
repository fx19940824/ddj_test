"""
配置管理测试
测试 GameState 的配置保存和加载功能
"""
import sys
from pathlib import Path
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import GameRegions


def test_game_regions():
    """测试 GameRegions 数据类"""
    print("Testing GameRegions...")
    regions = GameRegions()
    assert regions.hand_region is None
    assert regions.play_region is None
    assert regions.landlord_indicator is None

    regions.hand_region = (100, 200, 300, 400)
    assert regions.hand_region == (100, 200, 300, 400)
    print("  [OK] GameRegions works")


def test_config_json_format():
    """测试配置文件格式"""
    print("\nTesting config JSON format...")

    # 创建测试配置数据
    config_data = {
        'hand_region': [100, 200, 300, 400],
        'play_region': [500, 600, 700, 800],
        'landlord_indicator': [900, 1000, 100, 50],
        'player1_count': None,
        'player2_count': None,
    }

    # 测试JSON序列化
    json_str = json.dumps(config_data, ensure_ascii=False, indent=2)
    assert 'hand_region' in json_str
    assert 'landlord_indicator' in json_str

    # 测试JSON反序列化
    parsed = json.loads(json_str)
    assert parsed['hand_region'] == [100, 200, 300, 400]
    assert parsed['landlord_indicator'] == [900, 1000, 100, 50]

    # 测试转换为tuple
    hand_region = tuple(parsed['hand_region']) if parsed.get('hand_region') else None
    assert hand_region == (100, 200, 300, 400)

    landlord_region = tuple(parsed['landlord_indicator']) if parsed.get('landlord_indicator') else None
    assert landlord_region == (900, 1000, 100, 50)

    print("  [OK] Config JSON format works")


def test_existing_config():
    """测试现有配置文件（如果存在）"""
    print("\nTesting existing config file...")
    from config.settings import CONFIG_FILE

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  [OK] Config file loaded: {CONFIG_FILE.name}")
            if data.get('hand_region'):
                print(f"  - hand_region: {data['hand_region']}")
            if data.get('play_region'):
                print(f"  - play_region: {data['play_region']}")
            if data.get('landlord_indicator'):
                print(f"  - landlord_indicator: {data['landlord_indicator']}")
        except Exception as e:
            print(f"  [WARN] Config file exists but cannot be read: {e}")
    else:
        print("  [OK] No config file yet (fresh start)")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Config Management Tests")
    print("=" * 60)

    try:
        test_game_regions()
        test_config_json_format()
        test_existing_config()

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
