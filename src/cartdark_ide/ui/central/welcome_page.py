from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class WelcomePage(QWidget):
    """欢迎页"""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # Logo 占位符
        logo_label = QLabel("CartDark - IDE")
        logo_label.setStyleSheet("font-size: 48px; color: #888; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(logo_label)

        # 快捷键提示
        shortcuts = [
            ("打开资源", "⌘+P"),
            ("重新打开关闭的文件", "⌘+Shift+T"),
            ("在文件中搜索", "⌘+Shift+F"),
            ("构建并运行项目", "⌘+B"),
            ("启动或附加调试器", "F5")
        ]

        for action, shortcut in shortcuts:
            shortcut_widget = QWidget()
            shortcut_layout = QVBoxLayout(shortcut_widget)
            shortcut_layout.setContentsMargins(0, 5, 0, 5)

            action_label = QLabel(f"{action:<30} {shortcut}")
            action_label.setAlignment(Qt.AlignCenter)
            shortcut_layout.addWidget(action_label)

            self.layout.addWidget(shortcut_widget)