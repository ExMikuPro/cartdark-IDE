"""
CartDark IDE · state/settings_store.py
使用 QSettings 持久化 IDE 设置。
"""
from __future__ import annotations
from PySide6.QtCore import QSettings


class SettingsStore:
    """
    IDE 设置的统一读写入口。
    所有 key 集中定义为类常量，避免散落在各处硬编码字符串。
    """

    # ── key 常量 ──────────────────────────────
    KEY_LAST_PROJECT_LOCATION = "project/last_location"
    # 后续可在这里继续添加，例如：
    # KEY_THEME = "ui/theme"
    # KEY_RECENT_PROJECTS = "project/recent"

    def __init__(self):
        # 公司名/应用名决定配置文件的存储位置
        self._q = QSettings("CartDark", "CartDark IDE")

    # ── 通用读写 ──────────────────────────────

    def get(self, key: str, default=None):
        return self._q.value(key, default)

    def set(self, key: str, value) -> None:
        self._q.setValue(key, value)
        self._q.sync()

    # ── 具体字段快捷方法 ──────────────────────

    @property
    def last_project_location(self) -> str:
        import os
        fallback = os.path.expanduser("~")
        return self._q.value(self.KEY_LAST_PROJECT_LOCATION, fallback)

    @last_project_location.setter
    def last_project_location(self, path: str) -> None:
        self._q.setValue(self.KEY_LAST_PROJECT_LOCATION, path)
        self._q.sync()