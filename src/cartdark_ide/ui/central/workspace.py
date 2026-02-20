from PySide6.QtWidgets import QWidget, QVBoxLayout
from .welcome_page import WelcomePage

class Workspace(QWidget):
    """中央工作区"""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # 初始显示欢迎页
        self.welcome_page = WelcomePage()
        self.layout.addWidget(self.welcome_page)

        # 未来可以添加标签页或编辑器
