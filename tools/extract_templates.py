"""
从手牌截图中提取卡片模板工具
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image


def extract_cards_from_screenshot(image_path):
    """
    从截图中提取卡片

    Args:
        image_path: 截图路径
    """
    print("=" * 60)
    print("卡片模板提取工具")
    print("=" * 60)

    # 使用PIL读取图片（支持中文路径）
    try:
        pil_img = Image.open(image_path)
        img = np.array(pil_img)
        if len(img.shape) == 3 and img.shape[2] == 4:
            # RGBA -> RGB
            img = img[:, :, :3]
        elif len(img.shape) == 2:
            # 灰度 -> RGB
            img = np.stack([img] * 3, axis=2)
    except Exception as e:
        print(f"无法读取图片: {e}")
        return

    print(f"\n读取图片: {image_path}")
    print(f"图片尺寸: {img.shape[1]} x {img.shape[0]}")

    # 转灰度
    if len(img.shape) == 3:
        gray = np.mean(img, axis=2).astype(np.uint8)
    else:
        gray = img

    # 二值化
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"\n找到 {len(contours)} 个轮廓")

    # 过滤轮廓
    card_contours = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / h if h > 0 else 0

        # 假设卡片的宽高比在 0.5-0.8 之间
        if 500 < area < 10000 and 0.4 < aspect_ratio < 0.9:
            card_contours.append((x, y, w, h))
            print(f"  轮廓 {i}: 位置=({x},{y}), 大小={w}x{h}, 面积={area:.0f}")

    if not card_contours:
        print("\n未找到明显的卡片轮廓")
        print("\n建议:")
        print("1. 确保截图只包含手牌区域")
        print("2. 手牌与背景对比度要高")
        print("3. 先使用GUI版本手动选择区域")
        return

    # 按x坐标排序（从左到右）
    card_contours.sort(key=lambda c: c[0])

    print(f"\n找到 {len(card_contours)} 个可能的卡片区域")

    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "config" / "templates" / "cards"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存提取的卡片
    print("\n提取的卡片:")
    for i, (x, y, w, h) in enumerate(card_contours):
        # 稍微扩大一点区域
        margin = 5
        x2 = max(0, x - margin)
        y2 = max(0, y - margin)
        w2 = min(img.shape[1] - x2, w + margin * 2)
        h2 = min(img.shape[0] - y2, h + margin * 2)

        card_img = img[y2:y2 + h2, x2:x2 + w2]

        # 保存
        output_path = output_dir / f"card_{i:02d}.png"
        Image.fromarray(card_img).save(output_path)
        print(f"  {i+1}. 保存到: {output_path}")

    print("\n" + "=" * 60)
    print("提取完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 查看 config/templates/cards/ 目录下的 card_xx.png")
    print("2. 如果提取正确，将每张卡片重命名为: 3_spade.png, 10_heart.png 等")
    print("3. 运行GUI版本: python run.py")


# 延迟导入cv2，避免报错
try:
    import cv2
except ImportError:
    cv2 = None
    print("警告: opencv-python 未安装")


if __name__ == "__main__":
    if cv2 is None:
        print("请先安装依赖: pip install -r requirements.txt")
        sys.exit(1)

    # 尝试找到所有截图
    cards_dir = Path(__file__).parent.parent / "config" / "templates" / "cards"

    # 查找png文件
    screenshot_files = sorted(cards_dir.glob("*.png"))

    # 排除card_xx.png
    screenshot_files = [f for f in screenshot_files if not f.name.startswith("card_")]

    if not screenshot_files:
        print("未找到截图文件")
        print(f"请将截图保存到: {cards_dir}")
        sys.exit(1)

    print(f"找到 {len(screenshot_files)} 张截图:")
    for f in screenshot_files:
        print(f"  - {f.name}")

    # 处理第一张截图
    extract_cards_from_screenshot(screenshot_files[0])
