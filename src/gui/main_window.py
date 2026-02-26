"""
主窗口
"""
import sys
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QListWidget, QSplitter,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT
from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.ai.optimal_play import OptimalPlayEngine, PlaySuggestion
from src.capture.screen_capture import ScreenCapture
from src.ocr.card_detector import CardDetector


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
        self.screen_capture = ScreenCapture()
        self.card_detector = CardDetector()

        # 状态
        self.is_running = False
        self.is_paused = False

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)

        # 初始化UI
        self._init_ui()

        # 尝试加载配置
        self.game_state.load_config()

    def _init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.btn_settings = QPushButton("设置")
        self.btn_settings.clicked.connect(self.open_settings)
        toolbar.addWidget(self.btn_settings)

        self.btn_calibrate = QPushButton("校准")
        self.btn_calibrate.clicked.connect(self.start_calibration)
        toolbar.addWidget(self.btn_calibrate)

        self.btn_toggle = QPushButton("启动")
        self.btn_toggle.clicked.connect(self.toggle_running)
        toolbar.addWidget(self.btn_toggle)

        toolbar.addStretch()

        self.status_label = QLabel("状态: 停止")
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

        self.hand_label = QLabel("等待识别...")
        self.hand_label.setFont(QFont("Arial", 12))
        hand_layout.addWidget(self.hand_label)

        main_layout.addWidget(hand_group)

    def toggle_running(self):
        """切换运行状态"""
        if not self.is_running:
            # 检查是否已校准
            if not self.game_state.regions.hand_region:
                QMessageBox.warning(self, "提示", "请先进行校准！")
                return

            self.start()
        else:
            self.stop()

    def start(self):
        """启动"""
        self.is_running = True
        self.is_paused = False
        self.btn_toggle.setText("暂停")
        self.status_label.setText("状态: 运行中")
        self.status_label.setStyleSheet("color: green;")
        self.timer.start(500)  # 500ms刷新一次

    def stop(self):
        """停止"""
        self.is_running = False
        self.timer.stop()
        self.btn_toggle.setText("启动")
        self.status_label.setText("状态: 停止")
        self.status_label.setStyleSheet("color: black;")

    def update_game(self):
        """更新游戏状态"""
        if not self.is_running or self.is_paused:
            return

        # 1. 捕捉屏幕
        if self.game_state.regions.hand_region:
            hand_image = self.screen_capture.capture_region(self.game_state.regions.hand_region)
            if hand_image is not None:
                # 2. 识别手牌
                cards = self.card_detector.detect_cards(hand_image)
                if cards:
                    self.game_state.my_hand = cards
                    self._update_hand_display()

        # 3. 更新记牌器显示
        self._update_remaining_display()

        # 4. 生成出牌建议
        self._update_suggestions()

    def _update_hand_display(self):
        """更新手牌显示"""
        from src.game.card import cards_to_str
        self.hand_label.setText(cards_to_str(self.game_state.my_hand))

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

            item = self.suggestion_list.addItem(text)
            if i == 0:
                # 高亮首选
                self.suggestion_list.item(self.suggestion_list.count() - 1).setForeground(QColor("red"))

    def start_calibration(self):
        """开始校准"""
        QMessageBox.information(self, "校准", "校准功能开发中...\n\n请手动编辑配置文件设置区域。")

    def open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def closeEvent(self, event):
        """关闭事件"""
        self.game_state.save_config()
        self.screen_capture.close()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
