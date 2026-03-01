"""
屏幕捕捉模块
"""
import numpy as np
from PIL import Image
import mss
import mss.tools
from typing import Optional, Tuple
from pathlib import Path

from config.settings import SCREENSHOTS_DIR


class ScreenCapture:
    """屏幕捕捉器"""

    def __init__(self):
        # 不在 __init__ 中创建 mss 实例，避免跨线程问题
        self._last_frame = None

    def _get_sct(self):
        """获取新的 mss 实例（每次调用都创建新实例）"""
        return mss.mss()

    def capture_full_screen(self) -> np.ndarray:
        """
        捕捉全屏

        Returns:
            RGB图像数组
        """
        with self._get_sct() as sct:
            monitor = sct.monitors[0]
            img = sct.grab(monitor)
            frame = np.array(img)
            # BGRA -> RGB
            self._last_frame = frame[:, :, :3]
            return self._last_frame

    def capture_region(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        捕捉指定区域

        Args:
            region: (x, y, width, height)

        Returns:
            RGB图像数组
        """
        if not region:
            return None

        x, y, w, h = region
        if w <= 0 or h <= 0:
            return None

        monitor = {"top": y, "left": x, "width": w, "height": h}

        try:
            with self._get_sct() as sct:
                img = sct.grab(monitor)
                frame = np.array(img)
                self._last_frame = frame[:, :, :3]
                return self._last_frame
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to capture region {region}: {e}")
            return None

    def get_last_frame(self) -> Optional[np.ndarray]:
        """获取最后一帧"""
        return self._last_frame

    def save_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None,
                        filename: Optional[str] = None) -> str:
        """
        保存截图

        Args:
            region: 区域, None为全屏
            filename: 文件名, None自动生成

        Returns:
            保存的文件路径
        """
        if region:
            frame = self.capture_region(region)
        else:
            frame = self.capture_full_screen()

        if frame is None:
            return ""

        if not filename:
            import time
            filename = f"screenshot_{int(time.time())}.png"

        filepath = SCREENSHOTS_DIR / filename
        Image.fromarray(frame).save(filepath)
        return str(filepath)

    def get_monitor_size(self) -> Tuple[int, int]:
        """
        获取显示器尺寸

        Returns:
            (width, height)
        """
        with self._get_sct() as sct:
            monitor = sct.monitors[0]
            return monitor["width"], monitor["height"]

    def list_windows(self):
        """
        列出所有窗口(Windows)

        Returns:
            窗口列表
        """
        try:
            import win32gui

            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        windows.append((hwnd, title))
                return True

            windows = []
            win32gui.EnumWindows(callback, windows)
            return windows
        except ImportError:
            return []

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口位置和大小

        Args:
            hwnd: 窗口句柄

        Returns:
            (x, y, w, h)
        """
        try:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            w = right - x
            h = bottom - y
            return (x, y, w, h)
        except Exception:
            return None

    def capture_window(self, hwnd: int) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        截取指定窗口

        Args:
            hwnd: 窗口句柄

        Returns:
            (RGB图像数组, 窗口区域(x, y, w, h)) 或 None
        """
        rect = self.get_window_rect(hwnd)
        if not rect:
            return None
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return None

        # 使用 mss 截取窗口区域
        monitor = {"top": y, "left": x, "width": w, "height": h}

        try:
            with self._get_sct() as sct:
                img = sct.grab(monitor)
                frame = np.array(img)
                self._last_frame = frame[:, :, :3]
                return self._last_frame, rect
        except Exception:
            return None

    def find_window_by_title(self, title_contains: str) -> Optional[Tuple[int, int, int, int]]:
        """
        通过标题查找窗口

        Args:
            title_contains: 标题包含的字符串

        Returns:
            窗口区域 (x, y, w, h)
        """
        try:
            import win32gui

            def callback(hwnd, result):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title_contains in title:
                        rect = win32gui.GetWindowRect(hwnd)
                        x, y, right, bottom = rect
                        w = right - x
                        h = bottom - y
                        result.append((x, y, w, h))
                return True

            result = []
            win32gui.EnumWindows(callback, result)
            return result[0] if result else None
        except ImportError:
            return None

    def close(self):
        """关闭"""
        pass
