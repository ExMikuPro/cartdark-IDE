"""
CartDark IDE · ui/docks/assets_dock.py
资源面板停靠窗口。
"""
from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QTreeView
from PySide6.QtCore import Qt, Signal, QModelIndex

from ..models.assets_fs_model import AssetsFsModel
from ..delegates.assets_delegate import AssetsDelegate


class AssetsDock(QDockWidget):
    """资源面板"""

    # 用户激活了一个文件（双击或 Enter），发出其绝对路径
    file_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__("资源", parent)
        self.setMinimumWidth(230)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )

        self._model = AssetsFsModel(self)

        self._tree = QTreeView()
        self._tree.setHeaderHidden(True)
        self._tree.setModel(self._model)
        self._tree.setItemDelegate(AssetsDelegate(self._tree))
        self._tree.activated.connect(self._on_item_activated)

        self.setWidget(self._tree)

    # ── 公开 API ──────────────────────────────

    def load_project(self, project_root: str, project_name: str = ""):
        self._model.load_from_root(project_root, project_name)
        self._tree.expandToDepth(1)

    def close_project(self):
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["名称"])
        self._model._show_placeholder()

    def on_theme_changed(self):
        from ..icons import clear_cache
        clear_cache()
        self._model.reload_icons()

    # ── 内部槽 ────────────────────────────────

    def _on_item_activated(self, index: QModelIndex):
        item = self._model.itemFromIndex(index)
        if not item:
            return
        abs_path = getattr(item, "_abs_path", "")
        if abs_path:
            import os
            if os.path.isfile(abs_path):
                self.file_activated.emit(abs_path)