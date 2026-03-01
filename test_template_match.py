"""
测试卡片模板匹配功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from PIL import Image

from src.ocr.card_detector import CardDetector


def test_template_loading():
    """测试模板加载"""
    print("=" * 60)
    print("Test 1: Template Loading")
    print("=" * 60)

    detector = CardDetector()
    print(f"Loaded templates: {len(detector.templates)}")

    if detector.templates:
        print("\nTemplate list:")
        for name in sorted(detector.templates.keys()):
            size = detector.template_sizes.get(name, "unknown")
            print(f"  - {name}: {size}")
        return True
    else:
        print("No templates found!")
        return False


def test_hand_detection():
    """测试手牌截图识别"""
    print("\n" + "=" * 60)
    print("Test 2: Hand Screenshot Detection")
    print("=" * 60)

    detector = CardDetector()
    if not detector.templates:
        print("Skipped: No templates")
        return False

    # 降低阈值以提高识别率
    detector.set_threshold(0.6)

    template_dir = Path(__file__).parent / "config" / "templates" / "cards"
    screenshot_files = [
        template_dir / "我的手牌截图.png",
        template_dir / "我的手牌2.png",
        template_dir / "我的手牌3.png",
    ]

    success_count = 0
    for screenshot_file in screenshot_files:
        if not screenshot_file.exists():
            continue

        print(f"\nProcessing: {screenshot_file.name}")

        # 读取截图
        pil_img = Image.open(screenshot_file)
        img = np.array(pil_img)
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = img[:, :, :3]

        print(f"Image size: {img.shape[1]} x {img.shape[0]}")

        # 识别卡片
        cards = detector.detect_cards(img)

        if cards:
            print(f"Detected {len(cards)} cards:")
            for i, card in enumerate(cards, 1):
                print(f"  {i}. {card}")
            success_count += 1
        else:
            print("No cards detected")
            # 尝试更低的阈值
            print("Trying lower threshold...")
            detector.set_threshold(0.4)
            cards = detector.detect_cards(img)
            if cards:
                print(f"Detected {len(cards)} cards with lower threshold:")
                for i, card in enumerate(cards, 1):
                    print(f"  {i}. {card}")
                success_count += 1
            detector.set_threshold(0.6)

    return success_count > 0


def main():
    """主测试函数"""
    print("\nHappy Doudizhu - Template Matching Test\n")

    results = []
    results.append(("Template Loading", test_template_loading()))
    results.append(("Hand Detection", test_hand_detection()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
