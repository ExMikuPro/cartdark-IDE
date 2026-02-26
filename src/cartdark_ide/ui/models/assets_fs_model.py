from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
from ..icons import get_icon


class AssetsItem(QStandardItem):
    """资源树的基础节点"""
    def __init__(self, label: str, icon_name: str):
        super().__init__(label)
        self.setIcon(get_icon(icon_name))
        self.setEditable(False)


class AssetsFsModel(QStandardItemModel):
    """
    资源面板的数据模型。

    树结构：
      资源（根）
      ├── 依赖
      ├── 资源
      │   └── 主文件
      └── 输入
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["名称"])
        self._build_default_tree()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def load_project(self, project_data: dict):
        """
        从项目数据重建树。

        project_data 示例：
        {
            "dependencies": ["lib_a", "lib_b"],
            "resources": ["main.cd"],
            "inputs": ["keyboard", "gamepad"]
        }
        """
        self.clear()
        self.setHorizontalHeaderLabels(["名称"])

        root = self._make_root()

        for name in project_data.get("dependencies", []):
            root.child(0).appendRow(AssetsItem(name, "dependency"))

        for name in project_data.get("resources", []):
            root.child(1).appendRow(AssetsItem(name, "code"))

        for name in project_data.get("inputs", []):
            root.child(2).appendRow(AssetsItem(name, "input"))

    def reload_icons(self):
        """切换主题后刷新所有节点图标"""
        self._refresh_icons(self.invisibleRootItem())

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_default_tree(self):
        """构建默认示例树"""
        root = self._make_root()

        # 资源节点下添加示例主文件
        resources_node = root.child(1)
        resources_node.appendRow(AssetsItem("主文件", "code"))

    def _make_root(self) -> AssetsItem:
        """创建根节点及三个固定子节点，返回根节点"""
        root = AssetsItem("资源", "folder")
        root.appendRow(AssetsItem("依赖", "dependency"))
        root.appendRow(AssetsItem("资源", "folder"))
        root.appendRow(AssetsItem("输入", "input"))
        self.appendRow(root)
        return root

    def _refresh_icons(self, parent: QStandardItem):
        """递归刷新节点图标（暂存 icon_name 需在 setData 中保存）"""
        for row in range(parent.rowCount()):
            item = parent.child(row)
            if isinstance(item, AssetsItem):
                # AssetsItem 在构造时设置了图标，重新触发一次即可
                item.setIcon(item.icon())
            self._refresh_icons(item)