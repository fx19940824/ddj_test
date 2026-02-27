"""
主窗口
"""
import sys
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QListWidget, QSplitter,
    QMessageBox, QFileDialog, QTabWidget, QScrollArea, QGridLayout,
    QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QSpinBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT
from src.game.game_state import GameState
from src.game.card_tracker import CardTracker
from src.game.card import Card, sort_cards
from src.ai.optimal_play import OptimalPlayEngine, PlaySuggestion
from src.capture.screen_capture import ScreenCapture
from src.ocr.card_detector import CardDetector


class SimpleCardInputDialog(QDialog):
    """简单的卡片数量输入对话框"""

    def __init__(self, parent=None, title="选择卡片"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.card_counts = {}

        self._init_ui()
        self.setMinimumSize(400, 500)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 说明
        info = QLabel("请输入每张牌的数量（0-4，王牌0-1）")
        layout.addWidget(info)

        # 卡片输入区
        scroll = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        # 普通牌
        ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
        self.spinboxes = {}

        for rank in ranks:
            spin = QSpinBox()
            spin.setRange(0, 4)
            spin.setValue(0)
            self.spinboxes[rank] = spin
            form_layout.addRow(f"{rank}:", spin)

        # 王牌
        spin_small = QSpinBox()
        spin_small.setRange(0, 1)
        spin_small.setValue(0)
        self.spinboxes['joker_small'] = spin_small
        form_layout.addRow("小王:", spin_small)

        spin_big = QSpinBox()
        spin_big.setRange(0, 1)
        spin_big.setValue(0)
        self.spinboxes['joker_big'] = spin_big
        form_layout.addRow("大王:", spin_big)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_cards(self):
        """获取选中的卡片"""
        from src.game.card import Suit
        cards = []
        suit_map = [Suit.SPADE, Suit.HEART, Suit.CLUB, Suit.DIAMOND]

        for rank, spin in self.spinboxes.items():
            count = spin.value()
            for i in range(count):
                if rank == 'joker_small':
                    cards.append(Card(rank='joker_small'))
                elif rank == 'joker_big':
                    cards.append(Card(rank='joker_big'))
                else:
                    suit = suit_map[i % 4]
                    cards.append(Card(rank=rank, suit=suit))

        return sort_cards(cards)


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

        self.btn_input_hand = QPushButton("输入手牌")
        self.btn_input_hand.clicked.connect(self._open_hand_input)
        toolbar.addWidget(self.btn_input_hand)

        self.btn_add_played = QPushButton("记录出牌")
        self.btn_add_played.clicked.connect(self._open_played_input)
        toolbar.addWidget(self.btn_add_played)

        self.btn_last_play = QPushButton("上家出牌")
        self.btn_last_play.clicked.connect(self._open_last_play_input)
        toolbar.addWidget(self.btn_last_play)

        self.btn_reset = QPushButton("重置")
        self.btn_reset.clicked.connect(self._reset_game)
        toolbar.addWidget(self.btn_reset)

        toolbar.addStretch()

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

        self.hand_label = QLabel("请点击上方【输入手牌】按钮")
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

    def _open_hand_input(self):
        """打开手牌输入对话框"""
        dialog = SimpleCardInputDialog(self, "选择我的手牌")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cards = dialog.get_selected_cards()
            if cards:
                self.game_state.my_hand = cards
                self._update_hand_display()
                self._update_remaining_display()
                self._update_suggestions()
                self.status_label.setText(f"已输入 {len(cards)} 张手牌")

    def _open_played_input(self):
        """打开记录出牌对话框"""
        dialog = SimpleCardInputDialog(self, "记录已出牌")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cards = dialog.get_selected_cards()
            if cards:
                self.game_state.played_cards.extend(cards)
                self._update_remaining_display()
                self.status_label.setText(f"已记录 {len(cards)} 张出牌")

    def _open_last_play_input(self):
        """打开上家出牌对话框"""
        dialog = SimpleCardInputDialog(self, "上家出牌")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cards = dialog.get_selected_cards()
            self.game_state.current_play = cards
            self._update_last_play_display()
            self._update_suggestions()
            if cards:
                self.status_label.setText(f"已记录上家出牌: {len(cards)} 张")

    def _reset_game(self):
        """重置游戏"""
        reply = QMessageBox.question(self, "确认", "确定要重置吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.game_state.reset()
            self.card_tracker.reset()
            self._update_hand_display()
            self._update_last_play_display()
            self._update_remaining_display()
            self.suggestion_list.clear()
            self.status_label.setText("已重置")

    def toggle_running(self):
        """切换运行状态"""
        if not self.is_running:
            self.start()
        else:
            self.stop()

    def start(self):
        """启动"""
        self.is_running = True
        self.is_paused = False
        self.status_label.setText("运行中")
        self.status_label.setStyleSheet("color: green;")
        self.timer.start(500)

    def stop(self):
        """停止"""
        self.is_running = False
        self.timer.stop()
        self.status_label.setText("已停止")
        self.status_label.setStyleSheet("color: black;")

    def update_game(self):
        """更新游戏状态"""
        if not self.is_running or self.is_paused:
            return

        # 更新记牌器显示
        self._update_remaining_display()

        # 生成出牌建议
        self._update_suggestions()

    def _update_hand_display(self):
        """更新手牌显示"""
        from src.game.card import cards_to_str
        if self.game_state.my_hand:
            self.hand_label.setText(cards_to_str(self.game_state.my_hand))
        else:
            self.hand_label.setText("请点击上方【输入手牌】按钮")

    def _update_last_play_display(self):
        """更新上家出牌显示"""
        from src.game.card import cards_to_str
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

    def start_calibration(self):
        """开始校准"""
        QMessageBox.information(self, "校准", "校准功能开发中...")

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
