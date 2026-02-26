"""
文本OCR识别
"""
import numpy as np
import cv2
from typing import Optional, List
import logging

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)


class TextOCR:
    """文本OCR识别器"""

    def __init__(self):
        self.available = pytesseract is not None
        if not self.available:
            logger.warning("pytesseract not available, text OCR disabled")

    def recognize_text(self, image: np.ndarray) -> str:
        """
        识别图像中的文本

        Args:
            image: RGB图像

        Returns:
            识别到的文本
        """
        if not self.available:
            return ""

        try:
            # 预处理
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # OCR识别
            text = pytesseract.image_to_string(thresh, config='--psm 6')
            return text.strip()

        except Exception as e:
            logger.warning(f"OCR error: {e}")
            return ""

    def recognize_digits(self, image: np.ndarray) -> Optional[int]:
        """
        识别数字(用于剩余牌数)

        Args:
            image: 图像

        Returns:
            数字
        """
        text = self.recognize_text(image)

        # 提取数字
        digits = ''.join(c for c in text if c.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass

        return None

    def recognize_card_count(self, image: np.ndarray) -> Optional[int]:
        """
        识别剩余牌数

        Args:
            image: 牌数区域图像

        Returns:
            牌数
        """
        return self.recognize_digits(image)

    def set_tesseract_path(self, path: str):
        """
        设置tesseract路径

        Args:
            path: tesseract可执行文件路径
        """
        if pytesseract:
            pytesseract.pytesseract.tesseract_cmd = path
