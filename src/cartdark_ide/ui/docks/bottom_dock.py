from PySide6.QtWidgets import (
    QDockWidget, QWidget, QTabBar, QStackedWidget,
    QVBoxLayout, QHBoxLayout
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QSize, QSettings
from ..bottom_tabs.console_tab import ConsoleTab


def _load_dark() -> bool:
    """从 QSettings 读取上次保存的主题，默认暗色"""
    return QSettings("cartdark", "IDE").value("theme_dark", True, type=bool)


def save_theme(dark: bool):
    """保存主题，供 menus.py 调用"""
    QSettings("cartdark", "IDE").setValue("theme_dark", dark)


def _make_icon(shape: str, dark: bool) -> QIcon:
    color = "#aaaaaa" if dark else "#555555"
    size = 16
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(color), 1.5))
    p.setBrush(Qt.NoBrush)
    if shape == "console":
        p.drawText(0, 0, size, size, Qt.AlignCenter, ">_")
    elif shape == "curve":
        path = QPainterPath()
        path.moveTo(1, 12)
        path.cubicTo(4, 4, 8, 4, 10, 8)
        path.cubicTo(12, 12, 14, 4, 15, 4)
        p.drawPath(path)
    elif shape == "error":
        p.drawRoundedRect(2, 1, 12, 14, 2, 2)
        p.drawLine(8, 5, 8, 9)
        p.drawPoint(8, 11)
    elif shape == "search":
        p.drawEllipse(2, 2, 9, 9)
        p.drawLine(10, 10, 14, 14)
    elif shape == "bug":
        p.drawEllipse(4, 4, 8, 8)
        p.drawLine(8, 2, 8, 4)
        p.drawLine(3, 3, 4, 5)
        p.drawLine(13, 3, 12, 5)
    p.end()
    return QIcon(px)


def _tab_stylesheet(dark: bool) -> str:
    tab_color    = "#888888" if dark else "#666666"
    tab_selected = "#ffffff" if dark else "#1a1a1a"
    tab_hover    = "#cccccc" if dark else "#333333"
    tab_bg_hover = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.05)"
    return f"""
        QTabBar {{ border: none; outline: none; }}
        QTabBar::tab {{
            background: transparent;
            color: {tab_color};
            padding: 5px 14px 5px 10px;
            margin-right: 1px;
            min-width: 0px;
            min-height: 28px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{
            color: {tab_selected};
            border-bottom: 2px solid {tab_color};
            background: transparent;
        }}
        QTabBar::tab:hover:!selected {{
            color: {tab_hover};
            background: {tab_bg_hover};
        }}
    """


class BottomDock(QDockWidget):
    _SHAPES = ["console", "error", "search", "bug"]
    _LABELS = ["控制台", "构建错误", "搜索结果", "断点"]

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(260)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        
        # 获取当前主题状态
        dark = _load_dark()
# 显示默认标题栏
        # 移除了隐藏标题栏的代码，使用默认的标题栏

        self.setStyleSheet("QDockWidget { border: none; padding: 0px; }")

        container = QWidget()
        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setIconSize(QSize(14, 14))
        self.tab_bar.setMinimumHeight(32)

        tab_bar_row = QHBoxLayout()
        tab_bar_row.setContentsMargins(0, 0, 0, 0)
        tab_bar_row.setSpacing(0)
        tab_bar_row.addWidget(self.tab_bar)
        tab_bar_row.addStretch()

        self._separator = QWidget()
        self._separator.setFixedHeight(1)

        self.stack = QStackedWidget()
        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)

        outer_layout.addLayout(tab_bar_row)
        outer_layout.addWidget(self._separator)
        outer_layout.addWidget(self.stack)

        tabs = [ConsoleTab(), QWidget(), QWidget(), QWidget()]
        for shape, label, widget in zip(self._SHAPES, self._LABELS, tabs):
            self.tab_bar.addTab(_make_icon(shape, dark), label)
            self.stack.addWidget(widget)

        self.setWidget(container)
        self._apply(dark)

    def _apply(self, dark: bool):
        """外部直接调用此方法切换主题"""
        self.tab_bar.setStyleSheet(_tab_stylesheet(dark))
        sep_color = "#3a3a3a" if dark else "#dddddd"
        self._separator.setStyleSheet(f"background: {sep_color};")
        for i, shape in enumerate(self._SHAPES):
            self.tab_bar.setTabIcon(i, _make_icon(shape, dark))