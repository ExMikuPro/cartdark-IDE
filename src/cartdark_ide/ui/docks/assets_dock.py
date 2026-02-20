from PySide6.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
import os

def is_dark_mode():
    """检测是否为暗色模式"""
    from PySide6.QtGui import QPalette
    bg = QApplication.palette().color(QPalette.ColorRole.Window)
    return bg.lightness() < 128

def get_icon(name):
    """获取图标，在暗色模式下反转颜色"""
    # 构建图标路径
    icon_path = os.path.join(
        os.path.dirname(__file__),
        "..", "resources", "icons",
        f"{name}.png"
    )

    # 检查图标文件是否存在
    if not os.path.exists(icon_path):
        print(f"Icon file not found: {icon_path}")
        return QIcon()

    print(f"Loading icon: {icon_path}, dark mode: {is_dark_mode()}")

    # 加载原始图标
    pixmap = QPixmap(icon_path)

    # 如果是暗色模式，反转图标颜色
    if is_dark_mode():
        # 使用更可靠的颜色反转方法
        inverted_pixmap = QPixmap(pixmap.size())

        # 遍历每个像素，反转颜色
        for x in range(pixmap.width()):
            for y in range(pixmap.height()):
                color = pixmap.pixelColor(x, y)
                if color.alpha() > 0:  # 只处理非透明像素
                    # 反转 RGB 值，保持 alpha 不变
                    inverted_color = QColor(
                        255 - color.red(),
                        255 - color.green(),
                        255 - color.blue(),
                        color.alpha()
                    )
                    inverted_pixmap.setPixelColor(x, y, inverted_color)

        return QIcon(inverted_pixmap)

    return QIcon(pixmap)

class AssetsDock(QDockWidget):
    """资源面板"""
    def __init__(self):
        super().__init__("资源")
        self.setMinimumWidth(230)
        self.setFeatures(QDockWidget.DockWidgetMovable |
                         QDockWidget.DockWidgetFloatable |
                         QDockWidget.DockWidgetClosable)

        # 创建资源树
        self.assets_tree = QTreeWidget()
        self.assets_tree.setHeaderHidden(True)

        # 添加示例节点
        root = QTreeWidgetItem(self.assets_tree, ["资源"])
        root.setIcon(0, get_icon("文件夹"))

        dependencies = QTreeWidgetItem(root, ["依赖"])
        dependencies.setIcon(0, get_icon("依赖"))

        test = QTreeWidgetItem(root, ["测试"])
        test.setIcon(0, get_icon("文件夹"))

        input_folder = QTreeWidgetItem(test, ["输入"])
        input_folder.setIcon(0, get_icon("输入"))

        main_file = QTreeWidgetItem(input_folder, ["主文件"])
        main_file.setIcon(0, get_icon("代码文件"))

        self.assets_tree.expandAll()
        self.setWidget(self.assets_tree)