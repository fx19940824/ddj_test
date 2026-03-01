"""
自动识别管理器
统一管理手牌区和出牌区的识别
"""
import numpy as np
import cv2
from typing import List, Optional, Tuple
import logging

from config.settings import GameRegions
from src.game.card import Card, sort_cards
from src.capture.screen_capture import ScreenCapture
from src.ocr.card_detector import CardDetector

logger = logging.getLogger(__name__)


class AutoRecognizer:
    """自动识别管理器"""

    def __init__(self, regions: GameRegions):
        self.screen_capture = ScreenCapture()
        self.card_detector = CardDetector()
        self.regions = regions

        # 上一帧图像
        self.last_hand_image: Optional[np.ndarray] = None
        self.last_play_image: Optional[np.ndarray] = None

        # 上次识别结果
        self.last_recognized_hand: List[Card] = []
        self.last_recognized_play: List[Card] = []

        # 降低识别阈值以提高识别率
        self.card_detector.set_threshold(0.5)

    def update_regions(self, regions: GameRegions):
        """更新区域配置"""
        self.regions = regions

    def has_hand_region(self) -> bool:
        """是否有手牌区配置"""
        return self.regions.hand_region is not None

    def has_play_region(self) -> bool:
        """是否有出牌区配置"""
        return self.regions.play_region is not None

    def check_hand_region(self) -> Optional[List[Card]]:
        """
        检查手牌区，返回识别到的手牌（如果有变化）

        Returns:
            识别到的手牌，如果没有变化或没有配置则返回None
        """
        if not self.has_hand_region():
            return None

        # 捕捉手牌区
        hand_img = self._capture_region(self.regions.hand_region)
        if hand_img is None:
            return None

        # 检查是否有显著变化
        if self.last_hand_image is not None:
            if not self._image_changed(self.last_hand_image, hand_img, threshold=0.15):
                # 没有显著变化
                return None

        # 识别手牌
        cards = self.card_detector.detect_cards(hand_img)

        if cards:
            # 排序
            cards = sort_cards(cards)

            # 检查是否与上次识别结果相同
            if self._cards_equal(cards, self.last_recognized_hand):
                return None

            # 更新状态
            self.last_hand_image = hand_img
            self.last_recognized_hand = cards

            logger.info(f"Recognized hand: {cards}")
            return cards

        return None

    def check_play_region(self) -> Optional[List[Card]]:
        """
        检查出牌区，返回识别到的新牌（如果有变化）

        Returns:
            识别到的新牌，如果没有变化或没有配置则返回None
        """
        if not self.has_play_region():
            return None

        # 捕捉出牌区
        play_img = self._capture_region(self.regions.play_region)
        if play_img is None:
            return None

        # 检查是否有显著变化
        if self.last_play_image is not None:
            if not self._image_changed(self.last_play_image, play_img, threshold=0.1):
                # 没有显著变化
                return None

        # 识别出牌
        cards = self.card_detector.detect_cards(play_img)

        if cards:
            # 排序
            cards = sort_cards(cards)

            # 检查是否与上次识别结果相同
            if self._cards_equal(cards, self.last_recognized_play):
                return None

            # 更新状态
            self.last_play_image = play_img
            self.last_recognized_play = cards

            logger.info(f"Recognized play: {cards}")
            return cards

        # 如果没有识别到牌，但图像有变化，清空上次结果
        if self.last_play_image is not None:
            if self._image_changed(self.last_play_image, play_img, threshold=0.2):
                self.last_play_image = play_img
                if self.last_recognized_play:
                    self.last_recognized_play = []
                    return []

        return None

    def _capture_region(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """捕捉指定区域"""
        try:
            return self.screen_capture.capture_region(region)
        except Exception as e:
            logger.warning(f"Failed to capture region: {e}")
            return None

    def _image_changed(self, img1: np.ndarray, img2: np.ndarray,
                       threshold: float = 0.1) -> bool:
        """
        比较两幅图像是否有显著变化

        Args:
            img1: 第一幅图像
            img2: 第二幅图像
            threshold: 变化阈值 (0-1)

        Returns:
            是否有显著变化
        """
        try:
            # 确保尺寸相同
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

            # 转换为灰度
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            else:
                gray1 = img1

            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
            else:
                gray2 = img2

            # 计算绝对差分
            diff = cv2.absdiff(gray1, gray2)

            # 计算变化比例
            change_ratio = np.sum(diff > 30) / (diff.shape[0] * diff.shape[1])

            return change_ratio > threshold

        except Exception as e:
            logger.warning(f"Image comparison failed: {e}")
            return True

    def _cards_equal(self, cards1: List[Card], cards2: List[Card]) -> bool:
        """比较两组卡片是否相同"""
        if len(cards1) != len(cards2):
            return False

        for c1, c2 in zip(cards1, cards2):
            if c1.rank != c2.rank or c1.suit != c2.suit:
                return False

        return True

    def reset(self):
        """重置状态"""
        self.last_hand_image = None
        self.last_play_image = None
        self.last_recognized_hand = []
        self.last_recognized_play = []
