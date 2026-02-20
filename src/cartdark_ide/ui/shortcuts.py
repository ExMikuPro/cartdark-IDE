from PySide6.QtGui import QShortcut
from PySide6.QtCore import Qt

def register_shortcuts(window):
    """注册全局快捷键"""
    # 打开资源
    QShortcut(Qt.CTRL | Qt.Key_P, window, lambda: print("打开资源"))

    # 重新打开关闭的文件
    QShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_T, window, lambda: print("重新打开关闭的文件"))

    # 在文件中搜索
    QShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_F, window, lambda: print("在文件中搜索"))

    # 构建并运行项目
    QShortcut(Qt.CTRL | Qt.Key_B, window, lambda: print("构建并运行项目"))

    # 启动或附加调试器
    QShortcut(Qt.Key_F5, window, lambda: print("启动或附加调试器"))
