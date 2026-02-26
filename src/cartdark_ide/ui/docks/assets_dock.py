"""
CartDark IDE · ui/docks/assets_dock.py
资源面板停靠窗口。
"""
from PySide6.QtWidgets import QDockWidget, QTreeView
from PySide6.QtCore import Qt

from ..models.assets_fs_model import AssetsFsModel
from ..delegates.assets_delegate import AssetsDelegate


class AssetsDock(QDockWidget):
    """资源面板"""

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

        self.setWidget(self._tree)

    # ── 公开 API ──────────────────────────────

    def load_project(self, project_root: str, project_name: str = ""):
        """扫描 project_root 并填充资源树"""
        self._model.load_from_root(project_root, project_name)
        self._tree.expandToDepth(1)   # 默认展开一级

    def close_project(self):
        """清空资源树，回到空状态"""
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["名称"])
        self._model._show_placeholder()

    def on_theme_changed(self):
        """主题切换时刷新图标"""
        from ..icons import clear_cache
        clear_cache()
        self._model.reload_icons()