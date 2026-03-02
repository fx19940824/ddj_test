"""
主窗口 - 纯自动识别版本
"""
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QListWidget, QSplitter,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, GameRegions
from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.game.card import Card, cards_to_str
from src.ai.optimal_play import OptimalPlayEngine
from src.ocr.auto_recognizer import AutoRecognizer
from src.gui.calibration_dialog import CalibrationDialog
from src.gui.recognition_worker import RecognitionWorker


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("欢乐斗地主辅助")
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 核心组件
        self.game_state = GameState()
        self.card_tracker = CardTracker(self.game_state)
        self.ai_engine = OptimalPlayEngine()
        self.auto_recognizer = AutoRecognizer(self.game_state.regions)

        # 状态
        self.is_monitoring = False

        # 后台识别线程
        self.recognition_thread = QThread()
        self.recognition_worker = RecognitionWorker(self.auto_recognizer)
        self.recognition_worker.moveToThread(self.recognition_thread)

        # 连接信号
        self.recognition_worker.hand_recognized.connect(self._on_hand_recognized)
        self.recognition_worker.play_recognized.connect(self._on_play_recognized)
        self.recognition_worker.play_cleared.connect(self._on_play_cleared)
        self.recognition_worker.log_message.connect(self._on_log_message)
        self.recognition_worker.status_update.connect(self._on_status_update)
        self.recognition_worker.role_changed.connect(self._on_role_changed)

        # 定时器 - 触发后台识别
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.recognition_worker.do_recognition)

        # 识别计数
        self.recognition_count = 0

        # 初始化UI
        self._init_ui()

        # 尝试加载配置
        self.game_state.load_config()
        self.auto_recognizer.update_regions(self.game_state.regions)

    def _init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.btn_calibrate = QPushButton("校准区域")
        self.btn_calibrate.clicked.connect(self._open_calibration)
        toolbar.addWidget(self.btn_calibrate)

        self.btn_toggle_monitor = QPushButton("开始监控")
        self.btn_toggle_monitor.clicked.connect(self._toggle_monitoring)
        toolbar.addWidget(self.btn_toggle_monitor)

        self.btn_reset = QPushButton("重置")
        self.btn_reset.clicked.connect(self._reset_game)
        toolbar.addWidget(self.btn_reset)

        toolbar.addStretch()

        # 身份显示
        self.role_label = QLabel("身份: 待识别")
        self.role_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.role_label.setStyleSheet("color: gray;")
        toolbar.addWidget(self.role_label)

        toolbar.addSpacing(20)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        toolbar.addWidget(self.status_label)

        main_layout.addLayout(toolbar)

        # 主内容区 - 左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧 - 记牌器
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        remaining_group = QGroupBox("对手剩余牌统计")
        remaining_layout = QVBoxLayout(remaining_group)

        self.remaining_list = QListWidget()
        self.remaining_list.setFont(QFont("Consolas", 11))
        remaining_layout.addWidget(self.remaining_list)

        left_layout.addWidget(remaining_group)
        splitter.addWidget(left_panel)

        # 右侧 - 出牌建议
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        suggestion_group = QGroupBox("推荐出牌方案")
        suggestion_layout = QVBoxLayout(suggestion_group)

        self.suggestion_list = QListWidget()
        self.suggestion_list.setFont(QFont("Consolas", 11))
        suggestion_layout.addWidget(self.suggestion_list)

        right_layout.addWidget(suggestion_group)
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setSizes([250, 350])

        main_layout.addWidget(splitter)

        # 底部 - 当前手牌显示
        hand_group = QGroupBox("我的手牌")
        hand_layout = QHBoxLayout(hand_group)

        self.hand_label = QLabel("请先校准区域，然后点击【开始监控】")
        self.hand_label.setFont(QFont("Arial", 12))
        hand_layout.addWidget(self.hand_label)

        main_layout.addWidget(hand_group)

        # 上家出牌显示
        last_play_group = QGroupBox("上家出牌")
        last_play_layout = QHBoxLayout(last_play_group)

        self.last_play_label = QLabel("无")
        self.last_play_label.setFont(QFont("Arial", 12))
        last_play_layout.addWidget(self.last_play_label)

        main_layout.addWidget(last_play_group)

        # 日志显示
        log_group = QGroupBox("识别日志")
        log_layout = QVBoxLayout(log_group)

        self.log_list = QListWidget()
        self.log_list.setFont(QFont("Consolas", 9))
        self.log_list.setMaximumHeight(120)
        log_layout.addWidget(self.log_list)

        main_layout.addWidget(log_group)

    def _open_calibration(self):
        """打开校准对话框"""
        # 转换当前配置为字典
        initial_regions = {}
        if self.game_state.regions.hand_region:
            initial_regions['hand'] = list(self.game_state.regions.hand_region)
        if self.game_state.regions.play_region:
            initial_regions['play'] = list(self.game_state.regions.play_region)
        # 传递 landlord_indicator (转为 'landlord' 键)
        if self.game_state.regions.landlord_indicator:
            initial_regions['landlord'] = list(self.game_state.regions.landlord_indicator)

        dialog = CalibrationDialog(self, initial_regions)
        if dialog.exec() == CalibrationDialog.DialogCode.Accepted:
            regions = dialog.get_regions()

            # 更新游戏状态
            if 'hand' in regions:
                self.game_state.regions.hand_region = tuple(regions['hand'])
            if 'play' in regions:
                self.game_state.regions.play_region = tuple(regions['play'])
            # 保存 landlord 区域到 landlord_indicator
            if 'landlord' in regions:
                self.game_state.regions.landlord_indicator = tuple(regions['landlord'])

            # 更新识别器
            self.auto_recognizer.update_regions(self.game_state.regions)

            # 保存配置
            self.game_state.save_config()

            status_parts = []
            if self.game_state.regions.hand_region:
                status_parts.append("手牌区")
            if self.game_state.regions.play_region:
                status_parts.append("出牌区")
            # 显示地主标识区状态
            if self.game_state.regions.landlord_indicator:
                status_parts.append("地主标识区")

            if status_parts:
                self.status_label.setText(f"已校准: {', '.join(status_parts)}")
            else:
                self.status_label.setText("已校准")

    def _toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            # 停止监控
            self.monitor_timer.stop()
            self.recognition_worker.stop()
            self.recognition_thread.quit()
            self.recognition_thread.wait()
            self.is_monitoring = False
            self.btn_toggle_monitor.setText("开始监控")
            self.status_label.setText("已停止监控")
            self._add_log("已停止监控")
        else:
            # 开始监控
            if not self.auto_recognizer.has_hand_region() and not self.auto_recognizer.has_play_region():
                QMessageBox.warning(self, "提示", "请先校准区域！")
                return

            self.is_monitoring = True
            self.recognition_count = 0
            self.btn_toggle_monitor.setText("停止监控")
            self.status_label.setText("监控中...")
            self._add_log("开始监控...")
            self.recognition_worker.set_running(True)
            self.recognition_thread.start()
            self.monitor_timer.start(1000)  # 1000ms 间隔

    @pyqtSlot(list)
    def _on_hand_recognized(self, hand: list):
        """手牌识别完成（在主线程中执行）"""
        self.game_state.my_hand = hand
        self._update_hand_display()
        self._update_remaining_display()
        self._update_suggestions()
        self.status_label.setText(f"已识别手牌: {len(hand)} 张")

    @pyqtSlot(list)
    def _on_play_recognized(self, play: list):
        """出牌识别完成（在主线程中执行）"""
        self._process_new_play(play)

    @pyqtSlot()
    def _on_play_cleared(self):
        """出牌区清空（在主线程中执行）"""
        if self.game_state.current_play:
            self.game_state.current_play = []
            self._update_last_play_display()

    @pyqtSlot(str)
    def _on_log_message(self, message: str):
        """处理日志消息"""
        logger = __import__('logging').getLogger(__name__)
        logger.warning(message)
        self._add_log(message)

    @pyqtSlot(str)
    def _on_status_update(self, status: str):
        """处理状态更新"""
        self.status_label.setText(status)

    @pyqtSlot(bool)
    def _on_role_changed(self, is_landlord: bool):
        """处理身份变化"""
        from src.game.game_state import PlayerRole
        if is_landlord:
            self.game_state.my_role = PlayerRole.LANDLORD
            self.role_label.setText("身份: 地主")
            self.role_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.game_state.my_role = PlayerRole.PEASANT
            self.role_label.setText("身份: 农民")
            self.role_label.setStyleSheet("color: blue; font-weight: bold;")
        role_text = "地主" if is_landlord else "农民"
        self._add_log(f"身份识别为: {role_text}")

    def _add_log(self, message: str):
        """添加日志到UI"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_list.addItem(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.log_list.scrollToBottom()
        # 限制日志数量
        if self.log_list.count() > 50:
            self.log_list.takeItem(0)

    def _process_new_play(self, cards: list):
        """处理新识别到的牌"""
        # 判断是上家出牌还是我出牌
        # 简单策略：如果牌在我手里，就是我出牌；否则是上家出牌

        from src.game.card import cards_to_str

        def _find_card_by_rank(hand, target_card):
            """在手中查找牌面相同的牌（忽略花色）"""
            for i, hand_card in enumerate(hand):
                if hand_card.rank == target_card.rank:
                    return i
            return -1

        # 检查是否是我出的牌（所有牌都在我手里，只比较牌面）
        is_my_play = True
        indices_to_remove = []
        for card in cards:
            idx = _find_card_by_rank(self.game_state.my_hand, card)
            if idx == -1:
                is_my_play = False
                break
            indices_to_remove.append(idx)

        if is_my_play and self.game_state.my_hand:
            # 我出牌 - 从手牌移除，添加到已出牌
            # 按索引从大到小移除，避免索引变化问题
            for idx in sorted(indices_to_remove, reverse=True):
                removed_card = self.game_state.my_hand.pop(idx)
                self.game_state.played_cards.append(removed_card)

            self._update_hand_display()
            self._update_remaining_display()
            self.status_label.setText(f"我出牌: {cards_to_str(cards)}")
            self._add_log(f"我出牌: {cards_to_str(cards)}")

        else:
            # 上家出牌
            # 如果之前有牌，添加到已出牌
            if self.game_state.current_play:
                self.game_state.played_cards.extend(self.game_state.current_play)

            self.game_state.current_play = cards
            self._update_last_play_display()
            self._update_remaining_display()
            self._update_suggestions()
            self.status_label.setText(f"上家出牌: {cards_to_str(cards)}")
            self._add_log(f"上家出牌: {cards_to_str(cards)}")

    def _reset_game(self):
        """重置游戏"""
        reply = QMessageBox.question(self, "确认", "确定要重置吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 停止监控
            if self.is_monitoring:
                self._toggle_monitoring()

            self.game_state.reset()
            self.card_tracker.reset()
            self.auto_recognizer.reset()
            self.recognition_worker.reset()

            # 重置身份显示
            self.role_label.setText("身份: 待识别")
            self.role_label.setStyleSheet("color: gray;")

            self._update_hand_display()
            self._update_last_play_display()
            self._update_remaining_display()
            self.suggestion_list.clear()
            self.status_label.setText("已重置")

    def _update_hand_display(self):
        """更新手牌显示"""
        if self.game_state.my_hand:
            self.hand_label.setText(cards_to_str(self.game_state.my_hand))
        else:
            self.hand_label.setText("等待识别手牌...")

    def _update_last_play_display(self):
        """更新上家出牌显示"""
        if self.game_state.current_play:
            self.last_play_label.setText(cards_to_str(self.game_state.current_play))
        else:
            self.last_play_label.setText("无")

    def _update_remaining_display(self):
        """更新剩余牌显示"""
        self.remaining_list.clear()
        display = self.card_tracker.get_remaining_display()
        for line in display:
            self.remaining_list.addItem(line)

    def _update_suggestions(self):
        """更新出牌建议"""
        self.suggestion_list.clear()

        if not self.game_state.my_hand:
            return

        # 获取建议
        suggestions = self.ai_engine.get_suggestions(
            self.game_state.my_hand,
            self.game_state.current_play,
            self.game_state
        )

        for i, suggestion in enumerate(suggestions):
            prefix = "★首选" if i == 0 else f"方案{i+1}"
            if suggestion.is_pass:
                text = f"[{prefix}] 不出"
            else:
                text = f"[{prefix}] {suggestion}"

            self.suggestion_list.addItem(text)
            if i == 0:
                item = self.suggestion_list.item(self.suggestion_list.count() - 1)
                item.setForeground(QColor("red"))

    def closeEvent(self, event):
        """关闭事件"""
        if self.is_monitoring:
            self.monitor_timer.stop()
            self.recognition_worker.stop()
            self.recognition_thread.quit()
            self.recognition_thread.wait()
        self.game_state.save_config()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
