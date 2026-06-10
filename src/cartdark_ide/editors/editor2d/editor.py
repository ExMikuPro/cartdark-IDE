from __future__ import annotations

import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSplitter,
    QToolBar, QVBoxLayout, QWidget
)

from ...project.schema import CartProject
from ...ui.theme import theme
from .canvas import Canvas2D
from .layer_io import LayerFileError, load_layer, save_layer
from .panels import Hierarchy2D, Inspector2D
from .scene import Scene2D


class Editor2D(QWidget):
    modified_changed = Signal(bool)

    def __init__(
        self,
        file_path: str = "",
        parent=None,
        *,
        project_root: str = "",
        cart_project: CartProject | None = None,
    ):
        super().__init__(parent)
        self.file_path = os.path.abspath(file_path) if file_path else ""
        self._project_root = os.path.abspath(project_root) if project_root else self._infer_project_root()
        self._cart_project = cart_project
        self._modified = False
        self._scene = Scene2D()
        self._status = QLabel("")
        self._zoom = QLabel("100%")

        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._btn_select = self._toolbar.addAction("选择")
        self._btn_move = self._toolbar.addAction("移动")
        self._toolbar.addSeparator()
        self._btn_image = self._toolbar.addAction("新建图片")
        self._toolbar.addSeparator()
        self._btn_delete = self._toolbar.addAction("删除")
        self._btn_save = self._toolbar.addAction("保存")
        self._toolbar.addSeparator()
        self._toolbar.addWidget(QLabel("缩放 "))
        self._toolbar.addWidget(self._zoom)

        self._hierarchy = Hierarchy2D()
        self._canvas = Canvas2D()
        self._inspector = Inspector2D()
        self._canvas.set_project_root(self._project_root)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._hierarchy)
        splitter.addWidget(self._canvas)
        splitter.addWidget(self._inspector)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([240, 900, 280])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(splitter)
        layout.addWidget(self._status)

        self._btn_image.triggered.connect(self.add_image)
        self._btn_delete.triggered.connect(self.delete_selected)
        self._btn_save.triggered.connect(self.save)
        self._hierarchy.selection_requested.connect(self._select_node)
        self._canvas.selection_changed.connect(self._on_canvas_selection)
        self._canvas.node_moved.connect(self._on_node_changed)
        self._canvas.view_changed.connect(self._on_view_changed)
        self._inspector.node_changed.connect(self._on_node_changed)
        theme.changed.connect(lambda _: self.apply_theme())
        self.apply_theme()
        self.reload()

    @property
    def modified(self) -> bool:
        return self._modified

    def reload(self) -> None:
        default_width, default_height = self._display_size()
        try:
            result = load_layer(
                self.file_path,
                default_width=default_width,
                default_height=default_height,
            )
        except LayerFileError as e:
            QMessageBox.warning(self, "2D 编辑器", str(e))
            result = None

        self._scene = (
            result.scene
            if result
            else Scene2D(canvas_width=default_width, canvas_height=default_height)
        )
        width = self._scene.canvas_width
        height = self._scene.canvas_height
        self._hierarchy.set_scene(self._scene)
        self._canvas.set_scene(self._scene)
        self._inspector.set_node(None)
        if result and result.message:
            self._status.setText(result.message)
        elif self.file_path:
            self._status.setText(
                f"Layer: {self._rel_display_path(self.file_path)}  Canvas: {width}x{height}"
            )
        else:
            self._status.setText(f"未绑定 layer1，当前为空白编辑状态。Canvas: {width}x{height}")
        self._set_modified(False)

    def save(self) -> bool:
        path = self.file_path
        if not path:
            path = self._ask_save_path()
            if not path:
                return False
            self.file_path = path
        try:
            save_layer(path, self._scene)
        except LayerFileError as e:
            QMessageBox.critical(self, "保存 2D Layer", str(e))
            return False
        self._status.setText(f"已保存：{self._rel_display_path(path)}")
        self._set_modified(False)
        return True

    def add_image(self) -> None:
        node = self._scene.add_image()
        self._hierarchy.refresh(node.id)
        self._canvas.set_selected_node(node)
        self._inspector.set_node(node)
        self._set_modified(True)

    def delete_selected(self) -> None:
        node = self._canvas.selected_node
        if not node:
            return
        self._scene.remove(node)
        self._hierarchy.refresh()
        self._canvas.set_selected_node(None)
        self._inspector.set_node(None)
        self._set_modified(True)

    def apply_theme(self) -> None:
        self.setStyleSheet(f"background: {theme.BG_BASE}; color: {theme.FG_PRIMARY};")
        self._toolbar.setStyleSheet(
            f"QToolBar {{ background: {theme.BG_PANEL}; border-bottom: 1px solid {theme.BORDER}; spacing: 6px; }}"
            f"QToolButton {{ color: {theme.FG_PRIMARY}; padding: 4px 8px; }}"
            f"QToolButton:hover {{ background: {theme.BG_HOVER}; }}"
        )
        self._status.setStyleSheet(
            f"background: {theme.BG_PANEL}; color: {theme.FG_SECONDARY}; padding: 4px 10px; border-top: 1px solid {theme.BORDER};"
        )
        self._zoom.setStyleSheet(f"color: {theme.FG_PRIMARY};")

    def _select_node(self, node) -> None:
        self._canvas.set_selected_node(node)
        self._inspector.set_node(node)

    def _on_canvas_selection(self, node) -> None:
        self._hierarchy.set_selected_node(node)
        self._inspector.set_node(node)

    def _on_node_changed(self, node) -> None:
        selected = self._canvas.selected_node
        self._hierarchy.refresh(selected.id if selected else "")
        self._inspector.sync_from_node()
        self._canvas.update()
        self._set_modified(True)

    def _on_view_changed(self, zoom: float, pan_x: float, pan_y: float) -> None:
        self._zoom.setText(f"{int(zoom * 100)}%")

    def _set_modified(self, value: bool) -> None:
        if self._modified == value:
            return
        self._modified = value
        self.modified_changed.emit(value)

    def _infer_project_root(self) -> str:
        if not self.file_path:
            return ""
        current = os.path.dirname(self.file_path)
        while current and current != os.path.dirname(current):
            try:
                if any(name.endswith(".cart") for name in os.listdir(current)):
                    return current
            except OSError:
                return ""
            current = os.path.dirname(current)
        return ""

    def _ask_save_path(self) -> str:
        start = self._project_root or os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(self, "保存 Layer", start, "Layer (*.layer)")
        if not path:
            return ""
        if not path.lower().endswith(".layer"):
            path += ".layer"
        return os.path.abspath(path)

    def _display_size(self) -> tuple[int, int]:
        display = getattr(self._cart_project, "display", None)
        width = getattr(display, "width", 800)
        height = getattr(display, "height", 480)
        if not isinstance(width, int) or width <= 0:
            width = 800
        if not isinstance(height, int) or height <= 0:
            height = 480
        return width, height

    def _rel_display_path(self, path: str) -> str:
        if self._project_root:
            try:
                return os.path.relpath(path, self._project_root).replace(os.sep, "/")
            except ValueError:
                pass
        return path
