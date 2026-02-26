"""
CartDark IDE · services/project_service.py
项目的打开、关闭等业务逻辑，解耦 UI 与 IO 层。
"""
from __future__ import annotations

import os
from PySide6.QtCore import QObject, Signal

from ..project.io import load_cart, find_cart_file, ProjectLoadError
from ..project.schema import CartProject


class ProjectService(QObject):
    """
    项目服务。

    信号
    ----
    project_opened(CartProject, str)
        项目加载成功后发出，携带模型对象和项目根目录路径。
    project_closed()
        项目关闭时发出。
    error_occurred(str)
        发生可预期错误时发出错误信息。
    """

    project_opened = Signal(object, str)   # (CartProject, project_root)
    project_closed = Signal()
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_project: CartProject | None = None
        self._current_root: str = ""

    # ── 属性 ──────────────────────────────────

    @property
    def current_project(self) -> CartProject | None:
        return self._current_project

    @property
    def current_root(self) -> str:
        return self._current_root

    @property
    def is_open(self) -> bool:
        return self._current_project is not None

    # ── 公开操作 ──────────────────────────────

    def open_project_from_root(self, project_root: str) -> bool:
        """
        从项目根目录打开项目。
        成功时发出 project_opened 信号，失败时发出 error_occurred 信号。
        返回是否成功。
        """
        try:
            cart_path = find_cart_file(project_root)
            project = load_cart(cart_path)
        except ProjectLoadError as e:
            self.error_occurred.emit(str(e))
            return False

        self._current_project = project
        self._current_root = os.path.abspath(project_root)
        self.project_opened.emit(project, self._current_root)
        return True

    def open_project_from_cart(self, cart_path: str) -> bool:
        """
        直接从 .cart 文件路径打开项目。
        """
        project_root = os.path.dirname(os.path.abspath(cart_path))
        return self.open_project_from_root(project_root)

    def close_project(self):
        """关闭当前项目"""
        if self.is_open:
            self._current_project = None
            self._current_root = ""
            self.project_closed.emit()