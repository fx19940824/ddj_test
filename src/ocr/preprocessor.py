"""
图像预处理
"""
import numpy as np
import cv2
from typing import Tuple


class ImagePreprocessor:
    """图像预处理器"""

    def __init__(self):
        pass

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        Args:
            image: RGB图像

        Returns:
            处理后的图像
        """
        if image is None or image.size == 0:
            return image

        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # 增强对比度
        enhanced = self._enhance_contrast(gray)

        # 二值化
        binary = self._binarize(enhanced)

        return binary

    def _enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        """增强对比度"""
        # 直方图均衡化
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _binarize(self, gray: np.ndarray) -> np.ndarray:
        """二值化"""
        # 自适应阈值
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

    def resize(self, image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """调整大小"""
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)

    def crop(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """裁剪"""
        if y + h > image.shape[0] or x + w > image.shape[1]:
            return image
        return image[y:y + h, x:x + w]

    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """锐化"""
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)

    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """去噪"""
        return cv2.medianBlur(image, 3)
