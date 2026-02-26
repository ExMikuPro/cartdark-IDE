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

        # 模型
        self._model = AssetsFsModel(self)

        # 视图
        self._tree = QTreeView()
        self._tree.setHeaderHidden(True)
        self._tree.setModel(self._model)
        self._tree.setItemDelegate(AssetsDelegate(self._tree))
        self._tree.expandAll()

        self.setWidget(self._tree)

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def load_project(self, project_data: dict):
        """加载项目数据并刷新树"""
        self._model.load_project(project_data)
        self._tree.expandAll()

    def on_theme_changed(self):
        """主题切换时刷新图标"""
        from ..icons import clear_cache
        clear_cache()
        self._model.reload_icons()