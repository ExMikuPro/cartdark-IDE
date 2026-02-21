from PySide6.QtWidgets import QMainWindow, QApplication, QDockWidget
from PySide6.QtCore import Qt
from .app_style import setup_app_style
from .menus import create_menu_bar
from .statusbar import create_status_bar
from .central.workspace import Workspace
from .docks.assets_dock import AssetsDock
from .docks.changed_files_dock import ChangedFilesDock
from .docks.outline_dock import OutlineDock
from .docks.properties_dock import PropertiesDock
from .docks.bottom_dock import BottomDock
from .shortcuts import register_shortcuts

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CartDark - IDE")
        self.resize(1440, 900)

        # ★ qdarktheme 必须最先调用，在任何 widget 创建之前
        setup_app_style()

        create_menu_bar(self)
        create_status_bar(self)

        self.workspace = Workspace()
        self.setCentralWidget(self.workspace)

        self._create_left_panels()
        self._create_right_panels()
        self._create_bottom_panel()

        register_shortcuts(self)
        
        # 连接新建项目信号
        # 注意：actions 是在 create_menu_bar 中创建的，这里需要从 menu_bar 中获取
        # 或者在 create_menu_bar 函数中返回 actions
        # 为了避免修改太多，我们在 open_new_project_dialog 中直接创建对话框

    def _create_left_panels(self):
        self.assets_dock = AssetsDock()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.assets_dock)
        self.changed_files_dock = ChangedFilesDock()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.changed_files_dock)

    def _create_right_panels(self):
        self.outline_dock = OutlineDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.outline_dock)
        self.properties_dock = PropertiesDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _create_bottom_panel(self):
        # ★ 不再传 dark 参数，BottomDock 自己读 palette
        self.bottom_dock = BottomDock()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
    
    def open_new_project_dialog(self):
        """打开新建项目对话框"""
        from .dialogs.new_project_dialog import NewProjectDialog
        dialog = NewProjectDialog(self)
        dialog.project_created.connect(self.on_project_created)
        dialog.exec()
    
    def on_project_created(self, config):
        """项目创建回调"""
        # 这里可以处理项目创建后的逻辑
        print(f"Project created with config: {config}")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()