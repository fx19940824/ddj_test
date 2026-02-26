"""
校准工具 - 用于选择游戏区域
"""
import sys
from pathlib import Path
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CONFIG_FILE


def create_default_config():
    """创建默认配置文件"""
    default_config = {
        "hand_region": None,    # (x, y, width, height) - 手牌区域
        "play_region": None,    # 出牌区域
        "player1_count": None,  # 玩家1剩余牌数
        "player2_count": None,  # 玩家2剩余牌数
        "landlord_indicator": None,  # 地主标识
    }

    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"创建默认配置文件: {CONFIG_FILE}")
    else:
        print(f"配置文件已存在: {CONFIG_FILE}")

    print()
    print("配置说明:")
    print("- 使用截图工具获取坐标")
    print("- hand_region: 你的手牌显示区域")
    print("- play_region: 桌面出牌区域")
    print("- player1_count: 左侧玩家剩余牌数")
    print("- player2_count: 右侧玩家剩余牌数")


if __name__ == "__main__":
    create_default_config()
