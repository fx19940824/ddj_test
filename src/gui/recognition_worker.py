"""
后台识别工作器
在独立线程中执行识别，避免阻塞 UI
"""
from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional

from src.game.card import Card
from src.ocr.auto_recognizer import AutoRecognizer


class RecognitionWorker(QObject):
    """后台识别工作器"""

    # 信号：识别到手牌
    hand_recognized = pyqtSignal(list)
    # 信号：识别到出牌
    play_recognized = pyqtSignal(list)
    # 信号：出牌区清空
    play_cleared = pyqtSignal()
    # 信号：日志信息
    log_message = pyqtSignal(str)

    def __init__(self, auto_recognizer: AutoRecognizer):
        super().__init__()
        self.auto_recognizer = auto_recognizer
        self._running: bool = False
        self._my_hand_empty: bool = True  # 手牌是否为空（只识别一次）

    def stop(self):
        """停止识别"""
        self._running = False

    def reset(self):
        """重置状态"""
        self._my_hand_empty = True
        self.auto_recognizer.reset()

    def set_running(self, running: bool):
        """设置运行状态"""
        self._running = running

    def do_recognition(self):
        """
        执行一次识别（由定时器触发）

        注意：此方法在后台线程中执行
        """
        if not self._running:
            return

        try:
            # 1. 检查手牌区（只在开局时识别一次）
            if self._my_hand_empty and self.auto_recognizer.has_hand_region():
                hand = self.auto_recognizer.check_hand_region()
                if hand:
                    self._my_hand_empty = False
                    self.hand_recognized.emit(hand)

            # 2. 检查出牌区
            if self.auto_recognizer.has_play_region():
                play = self.auto_recognizer.check_play_region()
                if play is not None:
                    if play:
                        # 有新牌
                        self.play_recognized.emit(play)
                    else:
                        # 空牌（出牌区清空）
                        self.play_cleared.emit()

        except Exception as e:
            self.log_message.emit(f"识别错误: {e}")
