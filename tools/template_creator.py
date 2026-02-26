"""
模板创建工具 - 用于创建卡片模板图片
"""
import sys
from pathlib import Path
import cv2
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CARDS_TEMPLATE_DIR, CARD_RANKS, CARD_SUITS_SIMPLE


def create_dummy_templates():
    """
    创建占位模板 (实际使用时需要用户自己截图创建真实模板"""
    print("模板创建工具")
    print("=" * 50)
    print()
    print("使用说明:")
    print("1. 打开欢乐斗地主游戏")
    print("2. 截图并裁剪单张卡片")
    print("3. 保存到 config/templates/cards/ 目录")
    print("4. 文件命名格式: rank_suit.png")
    print("   例如: 3_spade.png, 10_heart.png, joker_small.png")
    print()
    print("牌面: 3,4,5,6,7,8,9,10,J,Q,K,A,2")
    print("花色: spade(黑桃), heart(红桃), club(梅花), diamond(方块)")
    print("王牌: joker_small, joker_big")
    print()

    # 确保目录存在
    if not CARDS_TEMPLATE_DIR.exists():
        CARDS_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {CARDS_TEMPLATE_DIR}")

    print(f"模板目录: {CARDS_TEMPLATE_DIR}")


if __name__ == "__main__":
    create_dummy_templates()
