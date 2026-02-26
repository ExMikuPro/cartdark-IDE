"""
CartDark IDE · ui/widgets/tab_header.py
自定义标签栏：可关闭标签、修改标记（·）、中键关闭、双击关闭。
支持亮/暗主题切换。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QScrollArea,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent

from ..theme import theme


class _Tab(QWidget):
    """单个标签项"""

    clicked = Signal(object)
    close_requested = Signal(object)

    def __init__(self, tab_id: str, title: str, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self._title = title
        self._modified = False
        self._active = False

        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.ArrowCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(4)

        self._dot = QLabel("●")
        self._dot.setFixedSize(8, 8)
        self._dot.setAlignment(Qt.AlignCenter)
        self._dot.setVisible(False)
        layout.addWidget(self._dot)

        self._label = QLabel(title)
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self._label)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(16, 16)
        self._close_btn.setFlat(True)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(lambda: self.close_requested.emit(self))
        layout.addWidget(self._close_btn)

        self._update_style()

    # ── 公开 API ──────────────────────────────

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self._label.setText(value)
        self._update_width()

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        self._modified = value
        self._dot.setVisible(value)

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        self._update_style()

    def apply_theme(self):
        self._update_style()

    # ── 事件 ──────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)
        elif event.button() == Qt.MiddleButton:
            self.close_requested.emit(self)
        super().mousePressEvent(event)

    # ── 内部 ──────────────────────────────────

    def _update_width(self):
        fm = self._label.fontMetrics()
        text_w = fm.horizontalAdvance(self._title)
        w = max(80, text_w + 10 + 8 + 4 + 4 + 16 + 4)
        self.setFixedWidth(w)

    def _update_style(self):
        t = theme

        # 修改点颜色
        self._dot.setStyleSheet(f"color: {t.ACCENT}; font-size: 8px;")

        # 关闭按钮
        close_style = f"""
            QPushButton {{
                color: {t.FG_SECONDARY};
                background: transparent;
                border: none;
                font-size: 11px;
                border-radius: 3px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {t.BTN_HOVER};
                color: {t.FG_PRIMARY};
            }}
        """

        if self._active:
            # 激活标签：稍亮背景 + 顶部强调色线
            bg     = t.BG_BASE
            border = t.BORDER
            top_c  = t.ACCENT
            self.setStyleSheet(f"""
                QWidget {{
                    background: {bg};
                    border: none;
                    border-top: 2px solid {top_c};
                    border-right: 1px solid {border};
                    border-left: 1px solid {border};
                }}
            """)
            self._label.setStyleSheet(
                f"QLabel {{ color: {t.FG_TITLE}; font-size: 13px; border: none; }}"
            )
        else:
            # 非激活标签：暗一点
            bg     = t.BG_NAV
            border = t.BORDER
            self.setStyleSheet(f"""
                QWidget {{
                    background: {bg};
                    border: none;
                    border-top: 2px solid transparent;
                    border-right: 1px solid {border};
                }}
            """)
            self._label.setStyleSheet(
                f"QLabel {{ color: {t.FG_SECONDARY}; font-size: 13px; border: none; }}"
            )

        self._close_btn.setStyleSheet(close_style)
        self._update_width()


class TabHeader(QWidget):
    """
    标签栏容器。

    信号
    ----
    tab_activated(tab_id)   用户点击了某个标签
    tab_closed(tab_id)      用户关闭了某个标签
    """

    tab_activated = Signal(str)
    tab_closed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(33)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(False)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background: transparent;")

        self._tab_container = QWidget()
        self._tab_container.setStyleSheet("background: transparent;")
        self._tab_container.setFixedHeight(33)
        self._tab_layout = QHBoxLayout(self._tab_container)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(0)
        self._tab_layout.addStretch()

        self._scroll.setWidget(self._tab_container)
        self._scroll.setFixedHeight(33)
        outer.addWidget(self._scroll)

        self._tabs: dict[str, _Tab] = {}
        self._active_id: str | None = None

        self._apply_theme()
        theme.changed.connect(lambda _: self._apply_theme())

    # ── 公开 API ──────────────────────────────

    def add_tab(self, tab_id: str, title: str):
        if tab_id in self._tabs:
            self.set_active(tab_id)
            return

        tab = _Tab(tab_id, title)
        tab.clicked.connect(lambda t: self._on_tab_clicked(t.tab_id))
        tab.close_requested.connect(lambda t: self._on_tab_close(t.tab_id))

        count = self._tab_layout.count()
        self._tab_layout.insertWidget(count - 1, tab)
        self._tabs[tab_id] = tab
        tab.show()
        self._resize_container()
        self.set_active(tab_id)

    def remove_tab(self, tab_id: str):
        if tab_id not in self._tabs:
            return
        tab = self._tabs.pop(tab_id)
        self._tab_layout.removeWidget(tab)
        tab.deleteLater()
        self._resize_container()

        if self._active_id == tab_id:
            self._active_id = None
            if self._tabs:
                self.set_active(next(reversed(self._tabs)))

    def set_active(self, tab_id: str):
        if tab_id not in self._tabs:
            return
        if self._active_id and self._active_id in self._tabs:
            self._tabs[self._active_id].active = False
        self._active_id = tab_id
        self._tabs[tab_id].active = True
        self._scroll_to(tab_id)

    def set_modified(self, tab_id: str, modified: bool):
        if tab_id in self._tabs:
            self._tabs[tab_id].modified = modified

    def set_title(self, tab_id: str, title: str):
        if tab_id in self._tabs:
            self._tabs[tab_id].title = title
            self._resize_container()

    @property
    def active_id(self) -> str | None:
        return self._active_id

    @property
    def tab_ids(self) -> list[str]:
        return list(self._tabs.keys())

    # ── 内部 ──────────────────────────────────

    def _apply_theme(self):
        t = theme
        self.setStyleSheet(f"background: {t.BG_NAV};")
        for tab in self._tabs.values():
            tab.apply_theme()

    def _on_tab_clicked(self, tab_id: str):
        self.set_active(tab_id)
        self.tab_activated.emit(tab_id)

    def _on_tab_close(self, tab_id: str):
        self.tab_closed.emit(tab_id)

    def _resize_container(self):
        total = sum(t.sizeHint().width() for t in self._tabs.values())
        self._tab_container.setFixedWidth(max(total + 4, self.width()))

    def _scroll_to(self, tab_id: str):
        if tab_id in self._tabs:
            tab = self._tabs[tab_id]
            self._scroll.ensureWidgetVisible(tab)

    def wheelEvent(self, event: QWheelEvent):
        bar = self._scroll.horizontalScrollBar()
        bar.setValue(bar.value() - event.angleDelta().y() // 2)