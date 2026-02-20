from PySide6.QtWidgets import QDockWidget, QWidget

class PropertiesDock(QDockWidget):
    """属性面板"""
    def __init__(self):
        super().__init__("属性")
        self.setMinimumWidth(200)
        self.setFeatures(QDockWidget.DockWidgetMovable |
                         QDockWidget.DockWidgetFloatable |
                         QDockWidget.DockWidgetClosable)

        # 创建内容部件
        content_widget = QWidget()
        self.setWidget(content_widget)
