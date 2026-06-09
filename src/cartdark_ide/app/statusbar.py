from PySide6.QtWidgets import QStatusBar

def create_status_bar(window):
    """创建状态栏"""
    status_bar = QStatusBar()
    status_bar.showMessage("就绪")
    window.setStatusBar(status_bar)
    return status_bar
