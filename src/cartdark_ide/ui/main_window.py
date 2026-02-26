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
from ..services.project_service import ProjectService


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

        # 项目服务
        self._project_service = ProjectService(self)
        self._project_service.project_opened.connect(self._on_project_opened)
        self._project_service.project_closed.connect(self._on_project_closed)
        self._project_service.error_occurred.connect(self._on_project_error)

    def _create_left_panels(self):
        self.assets_dock = AssetsDock()
        self.assets_dock.file_activated.connect(self.workspace.open_file)
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

    def open_open_project_dialog(self):
        """打开「打开项目」对话框"""
        from .dialogs.open_project_dialog import OpenProjectDialog
        dialog = OpenProjectDialog(self)
        dialog.project_selected.connect(self._project_service.open_project_from_root)
        dialog.exec()

    def on_project_created(self, config: dict):
        """新建项目后自动打开"""
        if config.get("options", {}).get("open_after_creation", True):
            project_root = config.get("project_root", "")
            if project_root:
                self._project_service.open_project_from_root(project_root)

    def _on_project_opened(self, project, project_root: str):
        """项目加载成功，更新各面板"""
        self.setWindowTitle(f"CartDark IDE — {project.name}")
        self.assets_dock.load_project(project_root, project.name)

    def _on_project_closed(self):
        """项目关闭，重置面板"""
        self.setWindowTitle("CartDark IDE")
        self.assets_dock.close_project()

    def _on_project_error(self, message: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "打开项目失败", message)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()