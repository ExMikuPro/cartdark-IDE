from __future__ import annotations

import os

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from ...ui.theme import theme
from .scene import Node2D, Scene2D


class Canvas2D(QWidget):
    selection_changed = Signal(object)
    node_moved = Signal(object)
    view_changed = Signal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._scene = Scene2D()
        self._selected_id = ""
        self._zoom = 1.0
        self._pan = QPointF(80.0, 60.0)
        self._last_mouse = QPoint()
        self._panning = False
        self._space_down = False
        self._drag_node: Node2D | None = None
        self._drag_offset = QPointF()
        self._project_root = ""
        self.apply_theme()
        theme.changed.connect(lambda _: self.apply_theme())

    @property
    def selected_node(self) -> Node2D | None:
        return self._scene.by_id(self._selected_id) if self._selected_id else None

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_project_root(self, project_root: str) -> None:
        self._project_root = project_root
        self.update()

    def set_scene(self, scene: Scene2D) -> None:
        self._scene = scene
        self._selected_id = ""
        self._zoom = 1.0
        self._pan = QPointF(80.0, 60.0)
        self.selection_changed.emit(None)
        self._emit_view_changed()
        self.update()

    def set_selected_node(self, node: Node2D | None) -> None:
        self._selected_id = node.id if node else ""
        self.selection_changed.emit(node)
        self.update()

    def screen_to_world(self, point: QPoint | QPointF) -> QPointF:
        return QPointF(
            (float(point.x()) - self._pan.x()) / self._zoom,
            (float(point.y()) - self._pan.y()) / self._zoom,
        )

    def world_to_screen(self, point: QPointF) -> QPointF:
        return QPointF(
            point.x() * self._zoom + self._pan.x(),
            point.y() * self._zoom + self._pan.y(),
        )

    def apply_theme(self) -> None:
        self.setStyleSheet(f"background: {theme.BG_BASE};")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.BG_BASE))
        self._draw_background(painter)
        self._draw_grid(painter)
        self._draw_axes(painter)
        self._draw_canvas_bounds(painter)
        self._draw_nodes(painter)
        self._draw_overlay(painter)

    def wheelEvent(self, event):
        old_zoom = self._zoom
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = max(0.15, min(6.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 0.001:
            return
        mouse = event.position()
        world_before = self.screen_to_world(mouse)
        self._zoom = new_zoom
        self._pan = QPointF(
            mouse.x() - world_before.x() * self._zoom,
            mouse.y() - world_before.y() * self._zoom,
        )
        self._emit_view_changed()
        self.update()

    def mousePressEvent(self, event):
        self.setFocus()
        self._last_mouse = event.position().toPoint()
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self._space_down
        ):
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
            return
        if event.button() == Qt.LeftButton:
            world = self.screen_to_world(event.position())
            node = self._hit_test(world)
            self.set_selected_node(node)
            if node:
                self._drag_node = node
                self._drag_offset = QPointF(world.x() - node.x, world.y() - node.y)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self._panning:
            delta = pos - self._last_mouse
            self._pan += QPointF(delta.x(), delta.y())
            self._last_mouse = pos
            self._emit_view_changed()
            self.update()
            return
        if self._drag_node:
            world = self.screen_to_world(event.position())
            self._drag_node.x = round(world.x() - self._drag_offset.x(), 2)
            self._drag_node.y = round(world.y() - self._drag_offset.y(), 2)
            self.node_moved.emit(self._drag_node)
            self.update()
            return
        self._last_mouse = pos

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._panning = False
            self._drag_node = None
            self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space_down = True
            self.setCursor(Qt.OpenHandCursor)
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected = self.selected_node
            if selected:
                self._scene.remove(selected)
                self.set_selected_node(None)
                self.node_moved.emit(None)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space_down = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().keyReleaseEvent(event)

    def _draw_background(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor("#171a1f" if theme.is_dark() else "#f4f6f8"))

    def _draw_grid(self, painter: QPainter) -> None:
        world_tl = self.screen_to_world(QPointF(0, 0))
        world_br = self.screen_to_world(QPointF(self.width(), self.height()))
        step = 50
        start_x = int(world_tl.x() // step * step)
        end_x = int(world_br.x() + step)
        start_y = int(world_tl.y() // step * step)
        end_y = int(world_br.y() + step)
        minor = QColor("#2a3038" if theme.is_dark() else "#dce2e8")
        painter.setPen(QPen(minor, 1))
        x = start_x
        while x <= end_x:
            sx = self.world_to_screen(QPointF(x, 0)).x()
            painter.drawLine(int(sx), 0, int(sx), self.height())
            x += step
        y = start_y
        while y <= end_y:
            sy = self.world_to_screen(QPointF(0, y)).y()
            painter.drawLine(0, int(sy), self.width(), int(sy))
            y += step

    def _draw_axes(self, painter: QPainter) -> None:
        origin = self.world_to_screen(QPointF(0, 0))
        painter.setPen(QPen(QColor("#f05d5e"), 2))
        painter.drawLine(0, int(origin.y()), self.width(), int(origin.y()))
        painter.setPen(QPen(QColor("#48b16e"), 2))
        painter.drawLine(int(origin.x()), 0, int(origin.x()), self.height())
        painter.setPen(QColor(theme.FG_SECONDARY))
        painter.drawText(int(origin.x()) + 6, int(origin.y()) - 6, "0,0")

    def _draw_canvas_bounds(self, painter: QPainter) -> None:
        tl = self.world_to_screen(QPointF(0, 0))
        br = self.world_to_screen(QPointF(self._scene.canvas_width, self._scene.canvas_height))
        rect = QRectF(tl, br)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(theme.ACCENT), 2))
        painter.drawRect(rect)

    def _draw_nodes(self, painter: QPainter) -> None:
        for node in self._scene.nodes:
            rect = self._node_screen_rect(node)
            selected = node.id == self._selected_id
            painter.setBrush(QBrush(QColor("#3f5366")))
            painter.setPen(QPen(QColor("#86c5ff"), 2 if selected else 1))
            painter.drawRect(rect)
            label = node.name or "image"
            if node.path and not self._asset_exists(node.path):
                label = "missing image"
            painter.setPen(QColor(theme.FG_PRIMARY))
            painter.drawText(rect, Qt.AlignCenter, label)
            if selected:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor("#ffd166"), 2, Qt.DashLine))
                painter.drawRect(rect.adjusted(-2, -2, 2, 2))

    def _draw_overlay(self, painter: QPainter) -> None:
        painter.setFont(QFont("Sans Serif", 10))
        painter.setPen(QColor(theme.FG_PRIMARY))
        world = self.screen_to_world(self._last_mouse)
        text = f"Zoom {int(self._zoom * 100)}%   World {world.x():.1f}, {world.y():.1f}"
        painter.drawText(12, self.height() - 14, text)

    def _node_screen_rect(self, node: Node2D) -> QRectF:
        tl = self.world_to_screen(QPointF(node.x, node.y))
        return QRectF(tl.x(), tl.y(), node.width * self._zoom, node.height * self._zoom)

    def _hit_test(self, world: QPointF) -> Node2D | None:
        for node in reversed(self._scene.nodes):
            if node.x <= world.x() <= node.x + node.width and node.y <= world.y() <= node.y + node.height:
                return node
        return None

    def _asset_exists(self, rel_path: str) -> bool:
        if not self._project_root:
            return True
        return os.path.isfile(os.path.join(self._project_root, rel_path))

    def _emit_view_changed(self) -> None:
        self.view_changed.emit(self._zoom, self._pan.x(), self._pan.y())
