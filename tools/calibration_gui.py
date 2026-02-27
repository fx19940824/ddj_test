"""
校准工具 - 图形界面版本
用于选择游戏区域和创建卡片模板
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QRect, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QImage


class CardTemplateWidget(QWidget):
    """卡片模板显示和选择"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.pixmap = None
        self.selections = []  # 选中的区域
        self.current_selection = None
        self.dragging = False
        self.drag_start = QPoint()
        self.setMinimumSize(800, 500)

    def load_image(self, filepath):
        """加载图片"""
        self.image = QPixmap(filepath)
        self.pixmap = self.image
        self.selections = []
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
            self.scale_x = scaled.width() / self.pixmap.width()
            self.scale_y = scaled.height() / self.pixmap.height()
            self.offset_x = x
            self.offset_y = y

            # 绘制已选区域
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            for sel in self.selections:
                rect = self._to_widget_rect(sel)
                painter.drawRect(rect)
                painter.drawText(rect.topLeft() + QPoint(5, 15), sel.get('name', ''))

            # 绘制当前选择
            if self.current_selection:
                pen = QPen(QColor(255, 255, 0), 2)
                painter.setPen(pen)
                rect = self._to_widget_rect(self.current_selection)
                painter.drawRect(rect)

    def _to_widget_rect(self, sel):
        """转换到widget坐标"""
        x = sel['x'] * self.scale_x + self.offset_x
        y = sel['y'] * self.scale_y + self.offset_y
        w = sel['w'] * self.scale_x
        h = sel['h'] * self.scale_y
        return QRect(int(x), int(y), int(w), int(h))

    def _to_image_rect(self, widget_x, widget_y, widget_w, widget_h):
        """转换到图片坐标"""
        x = (widget_x - self.offset_x) / self.scale_x
        y = (widget_y - self.offset_y) / self.scale_y
        w = widget_w / self.scale_x
        h = widget_h / self.scale_y
        return {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = event.position().toPoint()
            self.current_selection = {
                'x': event.position().x(),
                'y': event.position().y(),
                'w': 0,
                'h': 0,
                'name': ''
            }

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.dragging and self.current_selection:
            x = min(self.drag_start.x(), event.position().x())
            y = min(self.drag_start.y(), event.position().y())
            w = abs(event.position().x() - self.drag_start.x())
            h = abs(event.position().y() - self.drag_start.y())
            self.current_selection['x'] = x
            self.current_selection['y'] = y
            self.current_selection['w'] = w
            self.current_selection['h'] = h
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            if self.current_selection and self.current_selection['w'] > 20 and self.current_selection['h'] > 20:
                # 转换为图片坐标
                img_rect = self._to_image_rect(
                    self.current_selection['x'],
                    self.current_selection['y'],
                    self.current_selection['w'],
                    self.current_selection['h']
                )
                img_rect['name'] = f"card_{len(self.selections)}"
                self.selections.append(img_rect)
            self.current_selection = None
            self.update()


class CalibrationWindow(QMainWindow):
    """校准窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("卡片模板校准工具")
        self.setMinimumSize(1000, 700)
        self.current_image_path = None
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 工具栏
        toolbar = QHBoxLayout()

        btn_load = QPushButton("加载截图")
        btn_load.clicked.connect(self._load_screenshot)
        toolbar.addWidget(btn_load)

        btn_clear = QPushButton("清除选择")
        btn_clear.clicked.connect(self._clear_selections)
        toolbar.addWidget(btn_clear)

        btn_save = QPushButton("保存模板")
        btn_save.clicked.connect(self._save_templates)
        toolbar.addWidget(btn_save)

        toolbar.addStretch()

        help_label = QLabel("提示: 用鼠标框选每张牌，然后点击保存模板")
        toolbar.addWidget(help_label)

        layout.addLayout(toolbar)

        # 卡片显示区
        self.card_widget = CardTemplateWidget()
        layout.addWidget(self.card_widget, 1)

        # 保存的模板预览
        template_group = QGroupBox("已保存的模板")
        template_layout = QHBoxLayout(template_group)
        self.template_label = QLabel("暂无模板")
        template_layout.addWidget(self.template_label)
        layout.addWidget(template_group)

    def _load_screenshot(self):
        """加载截图"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择手牌截图",
            "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if filepath:
            self.current_image_path = Path(filepath)
            self.card_widget.load_image(filepath)

    def _clear_selections(self):
        """清除选择"""
        self.card_widget.selections = []
        self.card_widget.update()

    def _save_templates(self):
        """保存模板"""
        if not self.current_image_path:
            QMessageBox.warning(self, "提示", "请先加载截图")
            return

        if not self.card_widget.selections:
            QMessageBox.warning(self, "提示", "请先框选卡片")
            return

        from PIL import Image
        import numpy as np

        img = Image.open(self.current_image_path)
        img_np = np.array(img)

        output_dir = Path(__file__).parent.parent / "config" / "templates" / "cards"
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = 0
        for i, sel in enumerate(self.card_widget.selections):
            x, y, w, h = sel['x'], sel['y'], sel['w'], sel['h']
            if x < 0: x = 0
            if y < 0: y = 0
            if x + w > img_np.shape[1]: w = img_np.shape[1] - x
            if y + h > img_np.shape[0]: h = img_np.shape[0] - y

            card_img = img_np[y:y + h, x:x + w]
            if len(card_img.shape) == 3 and card_img.shape[2] == 4:
                card_img = card_img[:, :, :3]

            output_path = output_dir / f"card_{i:02d}.png"
            Image.fromarray(card_img).save(output_path)
            saved += 1

        QMessageBox.information(self, "完成", f"已保存 {saved} 个卡片模板到:\n{output_dir}")


def main():
    app = QApplication(sys.argv)
    window = CalibrationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
