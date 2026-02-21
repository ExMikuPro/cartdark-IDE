from PySide6.QtGui import QAction

def create_actions(window):
    """创建操作"""
    actions = {}

    # 文件操作
    actions["new"] = QAction("新建", window)
    actions["new_project"] = QAction("新建项目...", window)
    actions["open"] = QAction("打开", window)
    actions["save"] = QAction("保存", window)
    actions["exit"] = QAction("退出", window)

    # 编辑操作
    actions["undo"] = QAction("撤销", window)
    actions["redo"] = QAction("重做", window)
    actions["cut"] = QAction("剪切", window)
    actions["copy"] = QAction("复制", window)
    actions["paste"] = QAction("粘贴", window)

    # 构建操作
    actions["build"] = QAction("构建", window)
    actions["run"] = QAction("运行", window)

    return actions