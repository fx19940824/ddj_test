"""
卡片识别 - 模板匹配
"""
import numpy as np
import cv2
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging
from PIL import Image

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


def imread_pil(filepath: str) -> Optional[np.ndarray]:
    """使用PIL读取图片（支持中文路径）"""
    try:
        pil_img = Image.open(filepath)
        img = np.array(pil_img)
        # 转换为灰度
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                # RGBA -> RGB
                img = img[:, :, :3]
            # RGB -> GRAY
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return img
    except Exception as e:
        logger.warning(f"Failed to read image {filepath}: {e}")
        return None


class CardDetector:
    """卡片识别器"""

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.templates: Dict[str, np.ndarray] = {}
        self.template_sizes: Dict[str, Tuple[int, int]] = {}
        self.threshold = DEFAULT_OCR_CONFIG.template_match_threshold

        # 尝试加载模板
        self._load_templates()

    def _load_templates(self):
        """加载模板图片"""
        if not CARDS_TEMPLATE_DIR.exists():
            logger.warning(f"Template directory not found: {CARDS_TEMPLATE_DIR}")
            return

        loaded = 0
        for template_file in CARDS_TEMPLATE_DIR.glob("*.png"):
            name = template_file.stem
            # 跳过截图文件
            if name in ["我的手牌截图", "我的手牌2", "我的手牌3"]:
                continue

            try:
                # 使用PIL读取（支持中文路径）
                img = imread_pil(str(template_file))
                if img is not None:
                    self.templates[name] = img
                    self.template_sizes[name] = (img.shape[1], img.shape[0])
                    loaded += 1
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")

        logger.info(f"Loaded {loaded} card templates")

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

        # 如果没有模板，返回空列表
        if not self.has_templates():
            return []

        # 使用多尺度模板匹配
        return self._multi_scale_template_match(image)

    def _multi_scale_template_match(self, image: np.ndarray) -> List[Card]:
        """多尺度模板匹配识别多张卡片"""
        # 转换为灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        cards = []
        detected_positions = []  # 已检测到的位置，避免重复

        # 对每个模板进行匹配
        for name, template in self.templates.items():
            template_h, template_w = template.shape[:2]

            # 尝试不同的缩放比例
            scales = [0.9, 1.0, 1.1]
            best_match = None
            best_score = 0
            best_loc = None
            best_scale = 1.0

            for scale in scales:
                try:
                    # 缩放模板
                    if scale != 1.0:
                        new_w = int(template_w * scale)
                        new_h = int(template_h * scale)
                        if new_w < 10 or new_h < 10:
                            continue
                        scaled_template = cv2.resize(template, (new_w, new_h))
                    else:
                        scaled_template = template

                    # 模板匹配
                    result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)

                    if max_val > best_score:
                        best_score = max_val
                        best_match = name
                        best_loc = max_loc
                        best_scale = scale

                except Exception as e:
                    continue

            # 检查是否超过阈值且不与已检测的卡片重叠
            if best_match and best_score >= self.threshold:
                # 检查是否与已检测的位置重叠
                template_w_scaled = int(template_w * best_scale)
                template_h_scaled = int(template_h * best_scale)
                x, y = best_loc

                # 检查重叠
                overlap = False
                for (dx, dy, dw, dh) in detected_positions:
                    if (x < dx + dw and x + template_w_scaled > dx and
                        y < dy + dh and y + template_h_scaled > dy):
                        overlap = True
                        break

                if not overlap:
                    card = self._name_to_card(best_match)
                    if card:
                        cards.append(card)
                        detected_positions.append((x, y, template_w_scaled, template_h_scaled))
                        logger.debug(f"Detected {best_match} at ({x}, {y}) with score {best_score:.2f}")

        # 按从左到右排序卡片
        if detected_positions:
            # 合并位置和卡片，按x坐标排序
            combined = list(zip(detected_positions, cards))
            combined.sort(key=lambda item: item[0][0])
            cards = [card for (pos, card) in combined]

        return cards

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
            # 转换为灰度
            if len(card_image.shape) == 3:
                if card_image.shape[2] == 4:
                    card_image = card_image[:, :, :3]
                gray = cv2.cvtColor(card_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = card_image

            if not CARDS_TEMPLATE_DIR.exists():
                CARDS_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

            filepath = CARDS_TEMPLATE_DIR / f"{card_name}.png"
            # 使用PIL保存（支持中文路径）
            Image.fromarray(gray).save(filepath)

            self.templates[card_name] = gray
            self.template_sizes[card_name] = (gray.shape[1], gray.shape[0])
            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
