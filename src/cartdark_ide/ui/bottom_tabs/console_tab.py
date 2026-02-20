from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QPushButton, QLineEdit, QTextEdit, QHBoxLayout
from PySide6.QtCore import Qt

class ConsoleTab(QWidget):
    """控制台标签"""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QToolBar()
        toolbar.setOrientation(Qt.Horizontal)
        
        # 创建工具栏部件容器
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(5)
        
        # 筛选下拉按钮
        filter_button = QPushButton("筛选")
        filter_button.setStyleSheet("padding: 2px 8px;")
        toolbar_layout.addWidget(filter_button)
        
        # 搜索输入框
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("搜索")
        search_edit.setMinimumWidth(200)
        # 设置输入框占满剩余空间
        toolbar_layout.addWidget(search_edit, 1)  # 添加 stretch factor 1
        # 移除多余的 addStretch()，因为我们已经给 search_edit 添加了 stretch factor
        
        # 左右箭头按钮
        left_arrow = QPushButton("<")
        left_arrow.setStyleSheet("padding: 2px 6px;")
        toolbar_layout.addWidget(left_arrow)
        
        right_arrow = QPushButton(">")
        right_arrow.setStyleSheet("padding: 2px 6px;")
        toolbar_layout.addWidget(right_arrow)
        
        # 清除按钮
        clear_button = QPushButton("清除")
        clear_button.setStyleSheet("padding: 2px 8px;")
        toolbar_layout.addWidget(clear_button)
        
        # 将容器添加到工具栏
        toolbar.addWidget(toolbar_widget)
        
        self.layout.addWidget(toolbar)
        
        # 文本编辑框
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        # 移除硬编码的背景色，使用主题默认颜色
        self.layout.addWidget(self.console_text)