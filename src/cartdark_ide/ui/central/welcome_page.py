"""
CartDark IDE · ui/central/welcome_page.py
欢迎页，支持亮/暗主题切换。
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt

from ..theme import theme


class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.apply_theme()
        theme.changed.connect(lambda _: self.apply_theme())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        inner = QWidget()
        inner.setFixedWidth(480)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(32)
        inner_layout.setAlignment(Qt.AlignCenter)

        self._title = QLabel("CartDark - IDE")
        self._title.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(self._title)

        # 快捷键网格
        shortcuts = [
            ("打开资源",          "⌘+P"),
            ("重新打开关闭的文件", "⌘+Shift+T"),
            ("在文件中搜索",       "⌘+Shift+F"),
            ("构建并运行项目",     "⌘+B"),
            ("启动或附加调试器",   "F5"),
        ]

        self._grid_widget = QWidget()
        grid = QGridLayout(self._grid_widget)
        grid.setSpacing(0)
        grid.setHorizontalSpacing(48)
        grid.setVerticalSpacing(12)

        self._shortcut_labels = []
        for row, (action, key) in enumerate(shortcuts):
            lbl_action = QLabel(action)
            lbl_action.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_key    = QLabel(key)
            lbl_key.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(lbl_action, row, 0)
            grid.addWidget(lbl_key,    row, 1)
            self._shortcut_labels.append((lbl_action, lbl_key))

        inner_layout.addWidget(self._grid_widget, 0, Qt.AlignCenter)
        layout.addWidget(inner, 0, Qt.AlignCenter)

    def apply_theme(self):
        t = theme
        self.setStyleSheet(f"background: {t.BG_BASE};")

        self._title.setStyleSheet(
            f"color: {t.FG_MUTED}; font-size: 36px; font-weight: bold; letter-spacing: 1px;"
        )

        action_style = f"color: {t.FG_SECONDARY}; font-size: 13px;"
        key_style    = f"color: {t.FG_MUTED};    font-size: 13px;"
        for lbl_action, lbl_key in self._shortcut_labels:
            lbl_action.setStyleSheet(action_style)
            lbl_key.setStyleSheet(key_style)