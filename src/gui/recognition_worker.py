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
    # 信号：状态更新
    status_update = pyqtSignal(str)
    # 信号：身份变化（True=地主, False=农民）
    role_changed = pyqtSignal(bool)

    def __init__(self, auto_recognizer: AutoRecognizer):
        super().__init__()
        self.auto_recognizer = auto_recognizer
        self._running: bool = False
        self._my_hand_empty: bool = True  # 手牌是否为空
        self._recognition_count: int = 0
        self._last_role: Optional[bool] = None  # 上次识别的身份：None=未知, True=地主, False=农民

    def stop(self):
        """停止识别"""
        self._running = False

    def reset(self):
        """重置状态"""
        self._my_hand_empty = True
        self._recognition_count = 0
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

        self._recognition_count += 1

        try:
            # 发送状态更新
            self.status_update.emit(f"识别中... (#{self._recognition_count})")

            # 1. 检查手牌区（持续尝试直到识别成功）
            if self._my_hand_empty and self.auto_recognizer.has_hand_region():
                hand = self.auto_recognizer.check_hand_region()
                if hand:
                    self._my_hand_empty = False
                    self.log_message.emit(f"识别到手牌: {len(hand)} 张")
                    self.hand_recognized.emit(hand)
                else:
                    # 每5次记录一次日志，避免刷屏
                    if self._recognition_count % 5 == 0:
                        self.log_message.emit("正在识别手牌...")

            # 2. 检查出牌区
            if self.auto_recognizer.has_play_region():
                play = self.auto_recognizer.check_play_region()
                if play is not None:
                    if play:
                        # 有新牌
                        self.log_message.emit(f"识别到出牌: {len(play)} 张")
                        self.play_recognized.emit(play)
                    else:
                        # 空牌（出牌区清空）
                        self.log_message.emit("出牌区已清空")
                        self.play_cleared.emit()

            # 3. 检查地主标识区（每10次检查一次，避免过于频繁）
            if self.auto_recognizer.has_landlord_region() and self._recognition_count % 10 == 0:
                is_landlord = self.auto_recognizer.check_landlord_region()
                if is_landlord is not None and is_landlord != self._last_role:
                    self._last_role = is_landlord
                    role_text = "地主" if is_landlord else "农民"
                    self.log_message.emit(f"身份识别: {role_text}")
                    self.role_changed.emit(is_landlord)

        except Exception as e:
            self.log_message.emit(f"识别错误: {e}")
