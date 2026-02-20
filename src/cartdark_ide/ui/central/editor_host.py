from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit

class EditorHost(QWidget):
    """编辑器主机"""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # 临时使用 QPlainTextEdit 作为编辑器
        self.editor = QPlainTextEdit()
        self.layout.addWidget(self.editor)
