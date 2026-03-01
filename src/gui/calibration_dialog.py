"""
区域校准对话框
用于框选游戏区域（手牌区、出牌区）
"""
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QButtonGroup, QListWidget,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QImage

from src.capture.screen_capture import ScreenCapture


class WindowSelectDialog(QDialog):
    """窗口选择对话框"""

    def __init__(self, windows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择窗口")
        self.setMinimumSize(500, 400)
        self.selected_hwnd = None
        self.windows = windows

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 说明
        label = QLabel("请选择要截取的窗口：")
        layout.addWidget(label)

        # 窗口列表
        self.window_list = QListWidget()
        for hwnd, title in self.windows:
            self.window_list.addItem(f"{title} (HWND: {hwnd})")
        self.window_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.window_list, 1)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_double_click(self, item):
        """双击选择"""
        self._on_ok()

    def _on_ok(self):
        """确认选择"""
        current_row = self.window_list.currentRow()
        if current_row >= 0:
            self.selected_hwnd = self.windows[current_row][0]
            self.accept()


class RegionSelectWidget(QWidget):
    """区域选择组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image: Optional[QPixmap] = None
        self.pixmap: Optional[QPixmap] = None

        # 已选区域: {region_type: (x, y, w, h)}
        self.regions: Dict[str, Optional[Tuple[int, int, int, int]]] = {
            'hand': None,
            'play': None,
            'landlord': None,
        }

        self.current_region: str = 'hand'  # 当前要选择的区域
        self.selecting: bool = False
        self.selection_start: QPoint = QPoint()
        self.current_selection: Optional[Tuple[int, int, int, int]] = None

        # 区域颜色
        self.region_colors: Dict[str, QColor] = {
            'hand': QColor(0, 255, 0, 100),  # 绿色
            'play': QColor(0, 100, 255, 100),  # 蓝色
            'landlord': QColor(255, 100, 100, 100),  # 红色
        }

        self.region_names: Dict[str, str] = {
            'hand': '手牌区',
            'play': '出牌区',
            'landlord': '地主标识区',
        }

        self.setMinimumSize(800, 600)

    def set_image(self, image: np.ndarray):
        """设置图像（numpy数组）"""
        # 转换numpy数组为QPixmap - 使用PIL保存到临时文件再读取
        from PIL import Image as PILImage
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        pil_img = PILImage.fromarray(image)
        pil_img.save(temp_path)

        qimg = QPixmap(temp_path)
        self.image = qimg
        self.pixmap = qimg
        self.update()

        # 清理临时文件
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

    def set_current_region(self, region_type: str):
        """设置当前要选择的区域类型"""
        self.current_region = region_type
        self.current_selection = None
        self.update()

    def clear_selection(self, region_type: Optional[str] = None):
        """清除选择"""
        if region_type:
            self.regions[region_type] = None
        else:
            for key in self.regions:
                self.regions[key] = None
        self.current_selection = None
        self.update()

    def paintEvent(self, event):
        """绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(50, 50, 50))

        if self.pixmap:
            # 缩放图片以适应窗口
            scaled = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            # 保存缩放比例和偏移
            scale_x = scaled.width() / self.pixmap.width()
            scale_y = scaled.height() / self.pixmap.height()
            offset_x = x
            offset_y = y
            self._scale_info = (scale_x, scale_y, offset_x, offset_y)

            # 绘制已选区域
            for region_type, rect in self.regions.items():
                if rect:
                    widget_rect = self._to_widget_rect(rect, scale_x, scale_y, offset_x, offset_y)
                    color = self.region_colors[region_type]
                    painter.fillRect(widget_rect, color)
                    pen = QPen(QColor(color.red(), color.green(), color.blue()), 2)
                    painter.setPen(pen)
                    painter.drawRect(widget_rect)
                    painter.drawText(widget_rect.topLeft() + QPoint(5, 15),
                                     self.region_names[region_type])

            # 绘制当前选择
            if self.current_selection:
                widget_rect = self._to_widget_rect(
                    self.current_selection, scale_x, scale_y, offset_x, offset_y)
                pen = QPen(QColor(255, 255, 0), 2)
                painter.setPen(pen)
                painter.drawRect(widget_rect)

    def _to_widget_rect(self, rect: Tuple[int, int, int, int],
                        scale_x: float, scale_y: float,
                        offset_x: int, offset_y: int) -> QRect:
        """转换到widget坐标"""
        x, y, w, h = rect
        return QRect(
            int(x * scale_x + offset_x),
            int(y * scale_y + offset_y),
            int(w * scale_x),
            int(h * scale_y)
        )

    def _to_image_rect(self, widget_x: int, widget_y: int,
                       widget_w: int, widget_h: int) -> Tuple[int, int, int, int]:
        """转换到图片坐标"""
        if not hasattr(self, '_scale_info'):
            return (widget_x, widget_y, widget_w, widget_h)
        scale_x, scale_y, offset_x, offset_y = self._scale_info
        x = int((widget_x - offset_x) / scale_x)
        y = int((widget_y - offset_y) / scale_y)
        w = int(widget_w / scale_x)
        h = int(widget_h / scale_y)
        return (max(0, x), max(0, y), max(1, w), max(1, h))

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap:
            self.selecting = True
            self.selection_start = event.position().toPoint()
            self.current_selection = (
                event.position().x(),
                event.position().y(),
                0, 0
            )

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.selecting and self.current_selection:
            x1 = min(self.selection_start.x(), event.position().x())
            y1 = min(self.selection_start.y(), event.position().y())
            w = abs(event.position().x() - self.selection_start.x())
            h = abs(event.position().y() - self.selection_start.y())
            self.current_selection = (x1, y1, w, h)
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            if self.current_selection and self.current_selection[2] > 20 and self.current_selection[3] > 20:
                # 转换为图片坐标
                img_rect = self._to_image_rect(*self.current_selection)
                self.regions[self.current_region] = img_rect
            self.current_selection = None
            self.update()


class CalibrationDialog(QDialog):
    """校准对话框"""

    def __init__(self, parent=None, initial_regions=None):
        super().__init__(parent)
        self.setWindowTitle("区域校准工具")
        self.setMinimumSize(1000, 800)

        # 屏幕捕捉
        self.screen_capture = ScreenCapture()

        # 初始区域配置
        self.result_regions = initial_regions or {}

        # 窗口偏移量 (如果从窗口截图，需要保存偏移)
        self.window_offset = (0, 0)  # (x, y)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 区域选择组件
        self.region_widget = RegionSelectWidget()
        layout.addWidget(self.region_widget, 1)

        # 区域选择按钮
        region_btn_layout = QHBoxLayout()
        region_btn_layout.addWidget(QLabel("当前选择:"))

        self.region_group = QButtonGroup(self)

        self.btn_hand = QPushButton("手牌区")
        self.btn_hand.setCheckable(True)
        self.btn_hand.setChecked(True)
        self.btn_hand.clicked.connect(lambda: self._select_region('hand'))
        self.region_group.addButton(self.btn_hand)
        region_btn_layout.addWidget(self.btn_hand)

        self.btn_play = QPushButton("出牌区")
        self.btn_play.setCheckable(True)
        self.btn_play.clicked.connect(lambda: self._select_region('play'))
        self.region_group.addButton(self.btn_play)
        region_btn_layout.addWidget(self.btn_play)

        self.btn_landlord = QPushButton("地主标识区")
        self.btn_landlord.setCheckable(True)
        self.btn_landlord.clicked.connect(lambda: self._select_region('landlord'))
        self.region_group.addButton(self.btn_landlord)
        region_btn_layout.addWidget(self.btn_landlord)

        region_btn_layout.addStretch()
        layout.addLayout(region_btn_layout)

        # 工具栏
        toolbar = QHBoxLayout()

        self.btn_capture = QPushButton("截取屏幕")
        self.btn_capture.clicked.connect(self._capture_screen)
        toolbar.addWidget(self.btn_capture)

        self.btn_clear = QPushButton("清除选择")
        self.btn_clear.clicked.connect(self._clear_selection)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self._save_config)
        toolbar.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        toolbar.addWidget(self.btn_cancel)

        layout.addLayout(toolbar)

        # 提示
        help_label = QLabel("提示：先点击【截取屏幕】，然后选择要框选的区域类型，用鼠标在截图上框选")
        help_label.setFont(QFont("Arial", 9))
        layout.addWidget(help_label)

    def _select_region(self, region_type: str):
        """选择区域类型"""
        self.region_widget.set_current_region(region_type)

    def _capture_screen(self):
        """截取屏幕 - 先询问用户选择截图方式"""
        # 弹出选择对话框
        choice = QMessageBox.question(
            self,
            "选择截图方式",
            "请选择截图方式：\n\n"
            "• Yes: 截取全屏\n"
            "• No: 选择窗口",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if choice == QMessageBox.StandardButton.Yes:
            # 全屏截图
            self.window_offset = (0, 0)
            self._do_capture_fullscreen()
        elif choice == QMessageBox.StandardButton.No:
            # 窗口选择
            self._do_capture_window()

    def _do_capture_fullscreen(self):
        """截取全屏"""
        try:
            # 最小化对话框以避免遮挡
            self.showMinimized()

            # 延迟一小段时间确保窗口完全最小化
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300, self._finish_fullscreen_capture)

        except Exception as e:
            self.showNormal()
            QMessageBox.warning(self, "错误", f"截取屏幕失败：{str(e)}")

    def _finish_fullscreen_capture(self):
        """完成全屏截图"""
        try:
            img = self.screen_capture.capture_full_screen()
            if img is not None:
                self.region_widget.set_image(img)
            # 恢复窗口
            self.showNormal()
            self.raise_()
            self.activateWindow()
        except Exception as e:
            self.showNormal()
            QMessageBox.warning(self, "错误", f"截取屏幕失败：{str(e)}")

    def _do_capture_window(self):
        """选择窗口并截图"""
        try:
            # 获取窗口列表
            windows = self.screen_capture.list_windows()
            if not windows:
                QMessageBox.warning(self, "提示", "未找到可见窗口")
                return

            # 显示窗口选择对话框
            dialog = WindowSelectDialog(windows, self)
            if dialog.exec() != WindowSelectDialog.DialogCode.Accepted:
                return

            hwnd = dialog.selected_hwnd
            if hwnd is None:
                return

            # 最小化对话框
            self.showMinimized()

            # 延迟后截图
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._finish_window_capture(hwnd))

        except Exception as e:
            self.showNormal()
            QMessageBox.warning(self, "错误", f"窗口截图失败：{str(e)}")

    def _finish_window_capture(self, hwnd: int):
        """完成窗口截图"""
        try:
            result = self.screen_capture.capture_window(hwnd)
            if result is not None:
                img, rect = result
                x, y, w, h = rect
                self.window_offset = (x, y)
                self.region_widget.set_image(img)
            # 恢复窗口
            self.showNormal()
            self.raise_()
            self.activateWindow()
        except Exception as e:
            self.showNormal()
            QMessageBox.warning(self, "错误", f"窗口截图失败：{str(e)}")

    def _clear_selection(self):
        """清除选择"""
        self.region_widget.clear_selection()

    def _save_config(self):
        """保存配置"""
        # 验证是否有截图
        if self.region_widget.image is None:
            QMessageBox.warning(self, "提示", "请先截取屏幕")
            return

        # 收集结果，应用窗口偏移量
        self.result_regions = {}
        offset_x, offset_y = self.window_offset

        for region_type, rect in self.region_widget.regions.items():
            if rect:
                x, y, w, h = rect
                # 加上窗口偏移量，转换为屏幕坐标
                screen_rect = (x + offset_x, y + offset_y, w, h)
                self.result_regions[region_type] = list(screen_rect)

        if not self.result_regions:
            QMessageBox.warning(self, "提示", "请至少选择一个区域")
            return

        self.accept()

    def get_regions(self) -> dict:
        """获取选择的区域"""
        return self.result_regions


def main():
    """测试"""
    app = QApplication(sys.argv)
    dialog = CalibrationDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Regions:", dialog.get_regions())
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
