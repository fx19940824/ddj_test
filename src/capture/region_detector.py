"""
游戏区域检测
"""
from typing import Optional, Tuple, List
import numpy as np
import cv2

from config.settings import GameRegions


class RegionDetector:
    """区域检测器"""

    def __init__(self):
        self.regions = GameRegions()

    def set_region(self, name: str, region: Tuple[int, int, int, int]):
        """
        设置区域

        Args:
            name: 区域名称 ('hand', 'play', 'player1_count', 'player2_count', 'landlord')
            region: (x, y, w, h)
        """
        if name == 'hand':
            self.regions.hand_region = region
        elif name == 'play':
            self.regions.play_region = region
        elif name == 'player1_count':
            self.regions.player1_count = region
        elif name == 'player2_count':
            self.regions.player2_count = region
        elif name == 'landlord':
            self.regions.landlord_indicator = region

    def get_region(self, name: str) -> Optional[Tuple[int, int, int, int]]:
        """
        获取区域

        Args:
            name: 区域名称

        Returns:
            (x, y, w, h)
        """
        if name == 'hand':
            return self.regions.hand_region
        elif name == 'play':
            return self.regions.play_region
        elif name == 'player1_count':
            return self.regions.player1_count
        elif name == 'player2_count':
            return self.regions.player2_count
        elif name == 'landlord':
            return self.regions.landlord_indicator
        return None

    def get_all_regions(self) -> GameRegions:
        """获取所有区域"""
        return self.regions

    def set_all_regions(self, regions: GameRegions):
        """设置所有区域"""
        self.regions = regions

    def is_complete(self) -> bool:
        """检查是否所有区域都已设置"""
        return all([
            self.regions.hand_region,
            self.regions.play_region,
        ])

    def detect_cards_in_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> List[np.ndarray]:
        """
        在区域中检测卡片

        Args:
            image: 全屏图像
            region: 区域 (x, y, w, h)

        Returns:
            卡片图像列表
        """
        if region is None or image is None:
            return []

        x, y, w, h = region
        if x < 0 or y < 0 or x + w > image.shape[1] or y + h > image.shape[0]:
            return []

        roi = image[y:y + h, x:x + w]

        # 简单的卡片检测: 通过颜色和轮廓
        cards = self._extract_card_images(roi)
        return cards

    def _extract_card_images(self, roi: np.ndarray) -> List[np.ndarray]:
        """
        从ROI中提取卡片图像

        Args:
            roi: 感兴趣区域

        Returns:
            卡片图像列表
        """
        cards = []

        try:
            # 转灰度
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)

            # 二值化
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

            # 找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 过滤轮廓(假设卡片有一定大小)
            card_contours = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 500 < area < 5000:  # 根据实际调整
                    card_contours.append(cnt)

            # 提取卡片区域
            for cnt in card_contours:
                x, y, w, h = cv2.boundingRect(cnt)
                card_img = roi[y:y + h, x:x + w]
                cards.append(card_img)

        except Exception:
            pass

        return cards

    def reset(self):
        """重置"""
        self.regions = GameRegions()
