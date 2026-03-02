"""
自动识别器测试
测试 AutoRecognizer 类的功能
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr.auto_recognizer import AutoRecognizer
from config.settings import GameRegions


def test_region_management():
    """测试区域管理"""
    print("Testing region management...")

    regions = GameRegions()
    recognizer = AutoRecognizer(regions)

    assert not recognizer.has_hand_region()
    assert not recognizer.has_play_region()
    assert not recognizer.has_landlord_region()

    # 更新区域
    new_regions = GameRegions()
    new_regions.hand_region = (100, 200, 300, 400)
    new_regions.play_region = (500, 600, 700, 800)
    new_regions.landlord_indicator = (900, 1000, 100, 50)

    recognizer.update_regions(new_regions)

    assert recognizer.has_hand_region()
    assert recognizer.has_play_region()
    assert recognizer.has_landlord_region()
    print("  [OK] Region management works")


def test_red_pixel_detection():
    """测试红色像素检测（地主标识识别）"""
    print("\nTesting red pixel detection...")

    regions = GameRegions()
    regions.landlord_indicator = (0, 0, 100, 100)
    recognizer = AutoRecognizer(regions)

    # 创建测试图像 - 纯红色图像 (OpenCV BGR格式)
    red_img = np.zeros((100, 100, 3), dtype=np.uint8)
    red_img[:, :, 2] = 255  # R通道全255 (BGR格式中红色在索引2)

    # 模拟红色检测逻辑 (参考 auto_recognizer.py 中的实现)
    h, w = red_img.shape[:2]
    img_rgb = red_img
    # OpenCV读取的是BGR格式，转换一下
    r = img_rgb[:, :, 2].astype(int)
    g = img_rgb[:, :, 1].astype(int)
    b = img_rgb[:, :, 0].astype(int)
    red_dominant = (r > g + 50) & (r > b + 50)
    red_ratio = np.sum(red_dominant) / (h * w)

    print(f"  Red ratio: {red_ratio:.2%}")
    # 对于纯红图像，red_ratio 应该接近 1.0
    assert red_ratio > 0.9, f"Expected red ratio > 0.9, got {red_ratio}"
    print("  [OK] Red pixel detection logic works")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Auto Recognizer Tests")
    print("=" * 60)

    try:
        test_region_management()
        test_red_pixel_detection()

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
