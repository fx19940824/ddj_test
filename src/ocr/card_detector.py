"""
卡片识别 - 模板匹配
"""
import numpy as np
import cv2
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging

from config.settings import (
    CARDS_TEMPLATE_DIR,
    CARD_RANKS,
    JOKER_SMALL,
    JOKER_BIG,
    DEFAULT_OCR_CONFIG,
)
from src.game.card import Card, Suit
from .preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


class CardDetector:
    """卡片识别器"""

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.templates: Dict[str, np.ndarray] = {}
        self.template_size = (50, 80)  # 模板尺寸
        self.threshold = DEFAULT_OCR_CONFIG.template_match_threshold

        # 尝试加载模板
        self._load_templates()

    def _load_templates(self):
        """加载模板图片"""
        if not CARDS_TEMPLATE_DIR.exists():
            logger.warning(f"Template directory not found: {CARDS_TEMPLATE_DIR}")
            return

        for template_file in CARDS_TEMPLATE_DIR.glob("*.png"):
            try:
                img = cv2.imread(str(template_file), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    name = template_file.stem
                    self.templates[name] = cv2.resize(img, self.template_size)
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")

        logger.info(f"Loaded {len(self.templates)} card templates")

    def has_templates(self) -> bool:
        """是否有模板"""
        return len(self.templates) > 0

    def detect_cards(self, image: np.ndarray) -> List[Card]:
        """
        识别图像中的卡片

        Args:
            image: RGB图像

        Returns:
            识别到的卡片列表
        """
        if image is None or image.size == 0:
            return []

        # 预处理
        processed = self.preprocessor.preprocess(image)

        # 如果没有模板，返回空列表
        if not self.has_templates():
            return self._fallback_detection(processed)

        # 使用模板匹配
        return self._template_match_detection(processed)

    def _template_match_detection(self, image: np.ndarray) -> List[Card]:
        """使用模板匹配识别"""
        cards = []

        # 简单实现: 在图像中寻找单个卡片
        try:
            # 调整图像大小
            resized = cv2.resize(image, self.template_size)

            best_match = None
            best_score = 0

            for name, template in self.templates.items():
                result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_score and max_val >= self.threshold:
                    best_score = max_val
                    best_match = name

            if best_match:
                card = self._name_to_card(best_match)
                if card:
                    cards.append(card)

        except Exception as e:
            logger.warning(f"Template match error: {e}")

        return cards

    def _fallback_detection(self, image: np.ndarray) -> List[Card]:
        """无模板时的备用识别"""
        # 这里需要用户手动创建模板
        # 返回空列表
        return []

    def _name_to_card(self, name: str) -> Optional[Card]:
        """模板名称转卡片对象"""
        # 命名格式: rank_suit 或 joker_small/joker_big
        if name == JOKER_SMALL:
            return Card(rank=JOKER_SMALL)
        if name == JOKER_BIG:
            return Card(rank=JOKER_BIG)

        parts = name.split('_')
        if len(parts) >= 2:
            rank = parts[0]
            suit_name = parts[1]

            suit_map = {
                'spade': Suit.SPADE,
                'heart': Suit.HEART,
                'club': Suit.CLUB,
                'diamond': Suit.DIAMOND,
            }

            suit = suit_map.get(suit_name)
            if rank in CARD_RANKS:
                return Card(rank=rank, suit=suit)

        return None

    def detect_single_card(self, card_image: np.ndarray) -> Optional[Card]:
        """
        识别单张卡片

        Args:
            card_image: 单张卡片的图像

        Returns:
            Card对象或None
        """
        cards = self.detect_cards(card_image)
        return cards[0] if cards else None

    def set_threshold(self, threshold: float):
        """设置匹配阈值"""
        self.threshold = max(0.1, min(1.0, threshold))

    def create_template(self, card_image: np.ndarray, card_name: str) -> bool:
        """
        创建卡片模板

        Args:
            card_image: 卡片图像
            card_name: 模板名称

        Returns:
            是否成功
        """
        try:
            processed = self.preprocessor.preprocess(card_image)
            resized = cv2.resize(processed, self.template_size)

            if not CARDS_TEMPLATE_DIR.exists():
                CARDS_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

            filepath = CARDS_TEMPLATE_DIR / f"{card_name}.png"
            cv2.imwrite(str(filepath), resized)

            self.templates[card_name] = resized
            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
