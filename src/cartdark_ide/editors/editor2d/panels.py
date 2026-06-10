from __future__ import annotations

from contextlib import contextmanager

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QVBoxLayout, QWidget
)

from ...ui.theme import theme
from .scene import Node2D, Scene2D


class Hierarchy2D(QWidget):
    selection_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = Scene2D()
        self._list = QListWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        title = QLabel("节点列表")
        layout.addWidget(title)
        layout.addWidget(self._list)
        self._title = title
        self._list.currentItemChanged.connect(self._on_current_changed)
        self.apply_theme()
        theme.changed.connect(lambda _: self.apply_theme())

    def set_scene(self, scene: Scene2D) -> None:
        self._scene = scene
        self.refresh()

    def refresh(self, selected_id: str = "") -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for node in self._scene.nodes:
            item = QListWidgetItem(f"{node.name}  ({node.type})")
            item.setData(256, node.id)
            self._list.addItem(item)
            if node.id == selected_id:
                self._list.setCurrentItem(item)
        self._list.blockSignals(False)

    def set_selected_node(self, node: Node2D | None) -> None:
        self.refresh(node.id if node else "")

    def apply_theme(self) -> None:
        self._title.setStyleSheet(f"color: {theme.FG_TITLE}; font-weight: bold;")
        self._list.setStyleSheet(
            f"QListWidget {{ background: {theme.BG_PANEL}; color: {theme.FG_PRIMARY}; border: 1px solid {theme.BORDER}; }}"
            f"QListWidget::item:selected {{ background: {theme.BG_SELECTED}; }}"
        )

    def _on_current_changed(self, current, previous) -> None:
        if not current:
            self.selection_requested.emit(None)
            return
        node = self._scene.by_id(current.data(256))
        self.selection_requested.emit(node)


class Inspector2D(QWidget):
    node_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node: Node2D | None = None
        self._updating = False
        self._empty = QLabel("未选择对象")
        self._id = QLineEdit()
        self._name = QLineEdit()
        self._type = QLineEdit()
        self._path = QLineEdit()
        self._x = self._spin()
        self._y = self._spin()

        self._id.setReadOnly(True)
        self._type.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        self._title = QLabel("属性检查器")
        layout.addWidget(self._title)
        self._form = QFormLayout()
        self._form.setSpacing(8)
        self._form.addRow("id", self._id)
        self._form.addRow("name", self._name)
        self._form.addRow("type", self._type)
        self._form.addRow("path", self._path)
        self._form.addRow("x", self._x)
        self._form.addRow("y", self._y)
        layout.addLayout(self._form)
        layout.addWidget(self._empty)
        layout.addStretch()

        self._name.textEdited.connect(self._apply)
        self._path.textEdited.connect(self._apply)
        for widget in (self._x, self._y):
            widget.valueChanged.connect(self._apply)
        self.apply_theme()
        self.set_node(None)
        theme.changed.connect(lambda _: self.apply_theme())

    def set_node(self, node: Node2D | None) -> None:
        self._node = node
        with self._blocked():
            if not node:
                self._id.clear()
                self._name.clear()
                self._type.clear()
                self._path.clear()
                self._x.setValue(0)
                self._y.setValue(0)
            else:
                self._id.setText(node.id)
                self._name.setText(node.name)
                self._type.setText(node.type)
                self._path.setText(node.path)
                self._x.setValue(node.x)
                self._y.setValue(node.y)
        for widget in (
            self._id, self._name, self._type, self._path, self._x, self._y
        ):
            widget.setVisible(node is not None)
        for i in range(self._form.rowCount()):
            item = self._form.itemAt(i, QFormLayout.LabelRole)
            if item and item.widget():
                item.widget().setVisible(node is not None)
        self._empty.setVisible(node is None)

    def apply_theme(self) -> None:
        self._title.setStyleSheet(f"color: {theme.FG_TITLE}; font-weight: bold;")
        self._empty.setStyleSheet(f"color: {theme.FG_SECONDARY};")
        input_style = (
            f"background: {theme.BG_WIDGET_ALT}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BORDER_INPUT}; border-radius: 3px; padding: 3px 6px;"
        )
        for widget in (self._id, self._name, self._type, self._path, self._x, self._y):
            widget.setStyleSheet(input_style)

    def sync_from_node(self) -> None:
        self.set_node(self._node)

    def _spin(self, minimum: float = -100000.0) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, 100000.0)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        return spin

    def _apply(self) -> None:
        if self._updating or not self._node:
            return
        self._node.name = self._name.text()
        self._node.path = self._path.text()
        self._node.x = self._x.value()
        self._node.y = self._y.value()
        self.node_changed.emit(self._node)

    @contextmanager
    def _blocked(self):
        self._updating = True
        try:
            yield
        finally:
            self._updating = False
