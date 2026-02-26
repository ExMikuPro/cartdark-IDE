"""
CartDark IDE · ui/theme.py
全局主题颜色 token。

用法
----
from .theme import theme

# 读颜色
bg = theme.BG_BASE

# 监听切换
theme.changed.connect(my_widget.apply_theme)

# 切换主题
theme.set("light")   # or "dark"
"""
from __future__ import annotations
from PySide6.QtCore import QObject, Signal


class _Theme(QObject):
    changed = Signal(str)   # 发出新主题名 "dark" | "light"

    def __init__(self):
        super().__init__()
        self._name = "dark"
        self._apply("dark")

    @property
    def name(self) -> str:
        return self._name

    def set(self, name: str):
        if name not in ("dark", "light"):
            return
        self._apply(name)
        self._name = name
        self.changed.emit(name)

    def is_dark(self) -> bool:
        return self._name == "dark"

    def _apply(self, name: str):
        if name == "dark":
            # ── 暗色 token ────────────────────
            self.BG_BASE        = "#1e1e1e"   # 编辑器/页面底色
            self.BG_PANEL       = "#252526"   # 面板/表格背景
            self.BG_WIDGET      = "#2d2d2d"   # 输入框/ComboBox 背景
            self.BG_WIDGET_ALT  = "#3c3c3c"   # 稍亮的输入框背景
            self.BG_HOVER       = "#4e4e4e"   # hover 背景
            self.BG_SELECTED    = "#094771"   # 选中背景
            self.BG_NAV         = "#252526"   # 左侧导航背景
            self.BG_NAV_ACTIVE  = "#37373d"   # 导航选中行
            self.BG_NAV_HOVER   = "#2a2a2a"   # 导航 hover
            self.BG_HEADER      = "#2d2d2d"   # 表头背景
            self.BG_SCROLL      = "#1e1e1e"   # 滚动区域背景

            self.FG_PRIMARY     = "#cccccc"   # 主文字
            self.FG_SECONDARY   = "#888888"   # 次要文字 / 标签
            self.FG_MUTED       = "#555555"   # 禁用 / 分组标题
            self.FG_TITLE       = "#ffffff"   # 页面大标题
            self.FG_READONLY    = "#666666"   # 只读字段文字

            self.BORDER         = "#3c3c3c"   # 普通边框
            self.BORDER_INPUT   = "#555555"   # 输入框边框
            self.BORDER_FOCUS   = "#4fc3f7"   # 聚焦边框
            self.DIVIDER        = "#3c3c3c"   # 分割线
            self.DIVIDER_LIGHT  = "#333333"   # 次级分割线

            self.ACCENT         = "#4fc3f7"   # 强调色（蓝）
            self.ARROW          = "#888888"   # 下拉箭头颜色

            self.BTN_BG         = "#3c3c3c"
            self.BTN_HOVER      = "#4e4e4e"
            self.BTN_PRESSED    = "#2a2a2a"

            self.SECTION_SUB    = "#666666"
            self.NAV_GROUP      = "#555555"

        else:
            # ── 亮色 token ────────────────────
            self.BG_BASE        = "#f5f5f5"
            self.BG_PANEL       = "#ffffff"
            self.BG_WIDGET      = "#ffffff"
            self.BG_WIDGET_ALT  = "#f0f0f0"
            self.BG_HOVER       = "#e8e8e8"
            self.BG_SELECTED    = "#cce5ff"
            self.BG_NAV         = "#f0f0f0"
            self.BG_NAV_ACTIVE  = "#dce7f3"
            self.BG_NAV_HOVER   = "#e8e8e8"
            self.BG_HEADER      = "#ebebeb"
            self.BG_SCROLL      = "#f5f5f5"

            self.FG_PRIMARY     = "#1a1a1a"
            self.FG_SECONDARY   = "#555555"
            self.FG_MUTED       = "#aaaaaa"
            self.FG_TITLE       = "#000000"
            self.FG_READONLY    = "#999999"

            self.BORDER         = "#d4d4d4"
            self.BORDER_INPUT   = "#bbbbbb"
            self.BORDER_FOCUS   = "#0078d4"
            self.DIVIDER        = "#d4d4d4"
            self.DIVIDER_LIGHT  = "#e0e0e0"

            self.ACCENT         = "#0078d4"
            self.ARROW          = "#555555"

            self.BTN_BG         = "#e0e0e0"
            self.BTN_HOVER      = "#d0d0d0"
            self.BTN_PRESSED    = "#c0c0c0"

            self.SECTION_SUB    = "#888888"
            self.NAV_GROUP      = "#aaaaaa"


# 全局单例
theme = _Theme()