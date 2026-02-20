from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QTreeWidget, QHBoxLayout, QPushButton

class ChangedFilesDock(QDockWidget):
    """修改的文件面板"""
    def __init__(self):
        super().__init__("修改的文件")
        self.setMinimumWidth(230)
        self.setFeatures(QDockWidget.DockWidgetMovable |
                         QDockWidget.DockWidgetFloatable |
                         QDockWidget.DockWidgetClosable)

        # 创建内容部件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 创建修改的文件树
        self.changed_files_tree = QTreeWidget()
        self.changed_files_tree.setHeaderHidden(True)
        content_layout.addWidget(self.changed_files_tree)

        # 添加按钮
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)

        diff_button = QPushButton("差异")
        revert_button = QPushButton("恢复")

        buttons_layout.addWidget(diff_button)
        buttons_layout.addWidget(revert_button)

        content_layout.addWidget(buttons_widget)

        self.setWidget(content_widget)
