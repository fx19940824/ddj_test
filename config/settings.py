"""
配置文件 - 欢乐斗地主辅助程序
"""
from dataclasses import dataclass
from pathlib import Path


# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 模板图片目录
TEMPLATES_DIR = BASE_DIR / "config" / "templates"
CARDS_TEMPLATE_DIR = TEMPLATES_DIR / "cards"
UI_TEMPLATE_DIR = TEMPLATES_DIR / "ui_elements"

# 数据目录
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
TRAINING_DIR = DATA_DIR / "training"

# 配置文件路径
CONFIG_FILE = BASE_DIR / "config" / "config.json"


@dataclass
class GameRegions:
    """游戏区域配置"""
    hand_region: tuple = None  # 手牌区域 (x, y, w, h)
    play_region: tuple = None  # 出牌区域
    player1_count: tuple = None  # 玩家1剩余牌数
    player2_count: tuple = None  # 玩家2剩余牌数
    landlord_indicator: tuple = None  # 地主标识


@dataclass
class OCRConfig:
    """OCR配置"""
    template_match_threshold: float = 0.8
    capture_interval: float = 0.1  # 捕捉间隔(秒)
    enable_preprocessing: bool = True


# 卡片定义
CARD_RANKS = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
CARD_SUITS = ['♠', '♥', '♣', '♦']
CARD_SUITS_SIMPLE = ['spade', 'heart', 'club', 'diamond']

# 特殊牌
JOKER_SMALL = 'joker_small'  # 小王
JOKER_BIG = 'joker_big'      # 大王

# 牌型定义
PLAY_TYPES = {
    'SINGLE': '单张',
    'PAIR': '对子',
    'TRIPLE': '三张',
    'TRIPLE_1': '三带一',
    'TRIPLE_2': '三带二',
    'STRAIGHT': '顺子',
    'PAIR_STRAIGHT': '连对',
    'AIRPLANE': '飞机',
    'AIRPLANE_1': '飞机带单',
    'AIRPLANE_2': '飞机带对',
    'FOUR_2': '四带二',
    'BOMB': '炸弹',
    'ROCKET': '王炸',
}

# 牌面大小顺序（从小到大）
CARD_ORDER = {
    '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15,
    'joker_small': 16, 'joker_big': 17
}

# 默认配置
DEFAULT_GAME_REGIONS = GameRegions()
DEFAULT_OCR_CONFIG = OCRConfig()

# GUI配置
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 600
