from __future__ import annotations

import os

from PySide6.QtCore import QPoint, QPointF, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import QColor, QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QToolBar, QVBoxLayout, QWidget

from ..ui.theme import theme


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


def is_supported_image_path(file_path: str) -> bool:
    """Return True when the path should open in the image preview editor."""
    return os.path.splitext(file_path)[1].lower() in _supported_image_extensions()


def _supported_image_extensions() -> set[str]:
    extensions = set(SUPPORTED_IMAGE_EXTENSIONS)
    for fmt in QImageReader.supportedImageFormats():
        try:
            name = bytes(fmt).decode("ascii").lower()
        except (TypeError, UnicodeDecodeError):
            name = str(fmt).lower()
        if name:
            extensions.add(f".{name.lstrip('.')}")
    if ".jpeg" in extensions:
        extensions.add(".jpg")
    if ".jpg" in extensions:
        extensions.add(".jpeg")
    return extensions


class ImagePreviewCanvas(QWidget):
    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._pixmap = QPixmap()
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._fit_mode = True
        self._panning = False
        self._last_mouse = QPoint()
        self._message = ""
        self.apply_theme()
        theme.changed.connect(lambda _: self.apply_theme())

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._message = ""
        self.fit_to_window()

    def set_message(self, message: str) -> None:
        self._pixmap = QPixmap()
        self._message = message
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self.zoom_changed.emit(self._zoom)
        self.update()

    def fit_to_window(self) -> None:
        self._fit_mode = True
        self._apply_fit_zoom()
        self.update()

    def actual_size(self) -> None:
        if self._pixmap.isNull():
            return
        self._fit_mode = False
        self._zoom = 1.0
        self._center_image()
        self.zoom_changed.emit(self._zoom)
        self.update()

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom * 1.25)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom / 1.25)

    def set_zoom(self, zoom: float, anchor: QPointF | None = None) -> None:
        if self._pixmap.isNull():
            return
        old_zoom = self._zoom
        new_zoom = max(0.05, min(32.0, zoom))
        if abs(new_zoom - old_zoom) < 0.0001:
            return
        self._fit_mode = False
        if anchor is None:
            anchor = QPointF(self.width() / 2, self.height() / 2)
        image_point = QPointF(
            (anchor.x() - self._pan.x()) / old_zoom,
            (anchor.y() - self._pan.y()) / old_zoom,
        )
        self._zoom = new_zoom
        self._pan = QPointF(
            anchor.x() - image_point.x() * self._zoom,
            anchor.y() - image_point.y() * self._zoom,
        )
        self.zoom_changed.emit(self._zoom)
        self.update()

    def apply_theme(self) -> None:
        self.setStyleSheet(f"background: {theme.BG_BASE};")
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_mode:
            self._apply_fit_zoom()

    def wheelEvent(self, event):
        if self._pixmap.isNull():
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.set_zoom(self._zoom * factor, event.position())

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton and not self._pixmap.isNull():
            self._panning = True
            self._last_mouse = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._panning:
            pos = event.position().toPoint()
            delta = pos - self._last_mouse
            self._pan += QPointF(delta.x(), delta.y())
            self._last_mouse = pos
            self.update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor(theme.BG_BASE))

        if self._pixmap.isNull():
            if self._message:
                painter.setPen(QColor(theme.FG_SECONDARY))
                painter.drawText(self.rect().adjusted(24, 24, -24, -24), Qt.AlignCenter | Qt.TextWordWrap, self._message)
            return

        target = QRectF(
            self._pan,
            QSizeF(self._pixmap.width() * self._zoom, self._pixmap.height() * self._zoom),
        )
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))

    def _apply_fit_zoom(self) -> None:
        if self._pixmap.isNull():
            return
        margin = 24
        available_w = max(1, self.width() - margin * 2)
        available_h = max(1, self.height() - margin * 2)
        scale = min(
            available_w / max(1, self._pixmap.width()),
            available_h / max(1, self._pixmap.height()),
            1.0,
        )
        self._zoom = max(0.05, scale)
        self._center_image()
        self.zoom_changed.emit(self._zoom)

    def _center_image(self) -> None:
        image_w = self._pixmap.width() * self._zoom
        image_h = self._pixmap.height() * self._zoom
        self._pan = QPointF(
            (self.width() - image_w) / 2,
            (self.height() - image_h) / 2,
        )


class ImageViewerEditor(QWidget):
    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None, *, project_root: str = ""):
        super().__init__(parent)
        self.file_path = os.path.abspath(file_path)
        self._project_root = os.path.abspath(project_root) if project_root else ""
        self._modified = False
        self._image_size: tuple[int, int] | None = None
        self._error_message = ""

        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._fit_action = self._toolbar.addAction("适配")
        self._actual_action = self._toolbar.addAction("100%")
        self._toolbar.addSeparator()
        self._zoom_out_action = self._toolbar.addAction("-")
        self._zoom_in_action = self._toolbar.addAction("+")
        self._toolbar.addSeparator()
        self._zoom_label = QLabel("100%")
        self._toolbar.addWidget(self._zoom_label)

        self._canvas = ImagePreviewCanvas()
        self._status = QLabel("")
        self._status.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas, 1)
        layout.addWidget(self._status)

        self._fit_action.triggered.connect(self.fit_to_window)
        self._actual_action.triggered.connect(self.actual_size)
        self._zoom_out_action.triggered.connect(self.zoom_out)
        self._zoom_in_action.triggered.connect(self.zoom_in)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        theme.changed.connect(lambda _: self.apply_theme())
        self.apply_theme()
        self.reload()

    @property
    def modified(self) -> bool:
        return self._modified

    @property
    def image_size(self) -> tuple[int, int] | None:
        return self._image_size

    @property
    def error_message(self) -> str:
        return self._error_message

    def save(self) -> bool:
        return True

    def reload(self) -> None:
        self._image_size = None
        self._error_message = ""

        error = self._validate_path()
        if error:
            self._set_error(error)
            return

        try:
            with open(self.file_path, "rb"):
                pass
        except OSError as e:
            self._set_error(f"图片文件无法读取：{e}")
            return

        reader = QImageReader(self.file_path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            detail = reader.errorString() or "未知解码错误"
            self._set_error(f"图片解码失败：{detail}")
            return

        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            self._set_error("图片解码失败：无法创建预览图像")
            return

        self._image_size = (image.width(), image.height())
        self._canvas.set_pixmap(pixmap)
        self._update_info()

    def fit_to_window(self) -> None:
        self._canvas.fit_to_window()
        self._update_info()

    def actual_size(self) -> None:
        self._canvas.actual_size()
        self._update_info()

    def zoom_in(self) -> None:
        self._canvas.zoom_in()

    def zoom_out(self) -> None:
        self._canvas.zoom_out()

    def apply_theme(self) -> None:
        self.setStyleSheet(f"background: {theme.BG_BASE}; color: {theme.FG_PRIMARY};")
        self._toolbar.setStyleSheet(
            f"QToolBar {{ background: {theme.BG_PANEL}; border-bottom: 1px solid {theme.BORDER}; spacing: 6px; }}"
            f"QToolButton {{ color: {theme.FG_PRIMARY}; padding: 4px 8px; }}"
            f"QToolButton:hover {{ background: {theme.BG_HOVER}; }}"
            f"QLabel {{ color: {theme.FG_PRIMARY}; padding-left: 6px; }}"
        )
        self._status.setStyleSheet(
            f"background: {theme.BG_PANEL}; color: {theme.FG_SECONDARY}; padding: 4px 10px; border-top: 1px solid {theme.BORDER};"
        )
        self._canvas.apply_theme()

    def _validate_path(self) -> str:
        if self._project_root and not self._is_inside_project(self.file_path):
            return "图片路径不在当前项目目录内。"
        if not is_supported_image_path(self.file_path):
            return "图片格式不支持。支持格式：.png, .jpg, .jpeg, .bmp"
        if not os.path.exists(self.file_path):
            return "图片文件不存在。"
        if not os.path.isfile(self.file_path):
            return "图片路径不是文件。"
        return ""

    def _is_inside_project(self, file_path: str) -> bool:
        try:
            return os.path.commonpath([self._project_root, file_path]) == self._project_root
        except ValueError:
            return False

    def _set_error(self, message: str) -> None:
        self._error_message = message
        self._canvas.set_message(message)
        self._status.setText(f"{os.path.basename(self.file_path)}  |  {self._rel_path()}  |  {message}")
        self._zoom_label.setText("100%")

    def _on_zoom_changed(self, zoom: float) -> None:
        self._zoom_label.setText(f"{round(zoom * 100)}%")
        self._update_info()

    def _update_info(self) -> None:
        if self._error_message:
            return
        if not self._image_size:
            self._status.setText(f"{os.path.basename(self.file_path)}  |  {self._rel_path()}  |  未加载")
            return
        width, height = self._image_size
        zoom = round(self._canvas.zoom * 100)
        self._zoom_label.setText(f"{zoom}%")
        self._status.setText(
            f"{os.path.basename(self.file_path)}  |  {self._rel_path()}  |  {width} x {height}  |  {zoom}%"
        )

    def _rel_path(self) -> str:
        if self._project_root:
            try:
                return os.path.relpath(self.file_path, self._project_root).replace(os.sep, "/")
            except ValueError:
                pass
        return self.file_path
