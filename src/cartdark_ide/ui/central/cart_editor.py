"""
CartDark IDE · ui/central/cart_editor.py
.cart 工程文件的可视化编辑器。

布局：左侧导航（Project / Display / Bootstrap）+ 右侧表单。
"""
from __future__ import annotations

import json
import os

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QFileDialog, QComboBox, QSizePolicy,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


# ── 公用样式 ──────────────────────────────────

_NAV_STYLE = """
QListWidget {
    background: #252526;
    border: none;
    border-right: 1px solid #3c3c3c;
    outline: none;
    padding: 8px 0;
}
QListWidget::item {
    color: #aaaaaa;
    padding: 6px 20px;
    font-size: 13px;
}
QListWidget::item:selected {
    background: #37373d;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background: #2a2a2a;
    color: #cccccc;
}
/* 分组标题（禁用项） */
QListWidget::item:disabled {
    color: #555555;
    padding: 12px 20px 4px 20px;
    font-size: 11px;
    letter-spacing: 1px;
}
"""

_FIELD_LABEL_STYLE = "color: #888888; font-size: 13px; min-width: 160px;"

_INPUT_STYLE = """
QLineEdit {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #4fc3f7;
}
"""

_COMBO_STYLE = """
QComboBox {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 13px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
    background: #3c3c3c;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #888888;
    width: 0; height: 0;
}
QComboBox QAbstractItemView {
    background: #2d2d2d;
    color: #cccccc;
    border: 1px solid #555;
    selection-background-color: #094771;
    outline: none;
}
"""

_BROWSE_BTN_STYLE = """
QPushButton {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 10px;
    font-size: 13px;
    min-width: 32px;
}
QPushButton:hover { background: #4e4e4e; }
QPushButton:pressed { background: #2a2a2a; }
"""

_SECTION_TITLE_STYLE = "color: #ffffff; font-size: 18px; font-weight: bold;"
_SECTION_SUB_STYLE   = "color: #666666; font-size: 12px; margin-top: 2px;"
_DIVIDER_STYLE       = "background: #3c3c3c;"
_SPINBOX_STYLE = """
QSpinBox {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 13px;
    min-width: 80px;
}
QSpinBox:focus { border-color: #4fc3f7; }
QSpinBox::up-button, QSpinBox::down-button { width: 16px; background: #4a4a4a; border: none; }
"""
_CHECKBOX_STYLE = """
QCheckBox { color: #cccccc; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    background: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background: #4fc3f7;
    border-color: #4fc3f7;
}
"""


# ── 辅助：表单行构建器 ────────────────────────

def _make_scroll_page() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    """返回 (scroll, content_widget, layout)"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setStyleSheet("background: #1e1e1e; border: none;")

    content = QWidget()
    content.setStyleSheet("background: #1e1e1e;")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(32, 24, 32, 32)
    layout.setSpacing(0)
    scroll.setWidget(content)
    return scroll, content, layout


def _section_header(layout: QVBoxLayout, title: str, subtitle: str = ""):
    lbl = QLabel(title)
    lbl.setStyleSheet(_SECTION_TITLE_STYLE)
    layout.addWidget(lbl)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setStyleSheet(_SECTION_SUB_STYLE)
        layout.addWidget(sub)
    div = QFrame()
    div.setFrameShape(QFrame.HLine)
    div.setFixedHeight(1)
    div.setStyleSheet(_DIVIDER_STYLE)
    layout.addSpacing(12)
    layout.addWidget(div)
    layout.addSpacing(20)


def _field_row(layout: QVBoxLayout, label: str, widget: QWidget,
               extra: QWidget = None):
    """标签 + 控件（+ 可选附加控件）横排一行"""
    row = QHBoxLayout()
    row.setSpacing(12)
    lbl = QLabel(label)
    lbl.setStyleSheet(_FIELD_LABEL_STYLE)
    lbl.setFixedWidth(180)
    lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    row.addWidget(lbl)
    row.addWidget(widget)
    if extra:
        row.addWidget(extra)
    row.addStretch()
    layout.addLayout(row)
    layout.addSpacing(14)


# ── 各 Section 页面 ───────────────────────────

class _ProjectPage(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        scroll, _, layout = _make_scroll_page()

        _section_header(layout, "Project", "工程基本信息")

        self._name    = QLineEdit(); self._name.setStyleSheet(_INPUT_STYLE)
        self._id      = QLineEdit(); self._id.setStyleSheet(_INPUT_STYLE)
        self._id.setReadOnly(True)
        self._id.setStyleSheet(_INPUT_STYLE + "QLineEdit { color: #666666; }")
        self._template = QComboBox(); self._template.setStyleSheet(_COMBO_STYLE)
        self._template.addItems(["blank", "cartdark_os"])

        _field_row(layout, "Name",     self._name)
        _field_row(layout, "Template", self._template)
        _field_row(layout, "ID",       self._id)

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._name.textChanged.connect(self.changed)
        self._template.currentIndexChanged.connect(self.changed)

    def load(self, data: dict):
        p = data.get("project", {})
        self._name.setText(p.get("name", ""))
        self._id.setText(p.get("id", ""))
        idx = self._template.findText(p.get("template", "blank"))
        self._template.setCurrentIndex(max(0, idx))

    def save_into(self, data: dict):
        data.setdefault("project", {})
        data["project"]["name"]     = self._name.text()
        data["project"]["template"] = self._template.currentText()
        # id 只读，不修改


class _DisplayPage(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        scroll, _, layout = _make_scroll_page()

        _section_header(layout, "Display", "显示参数")

        self._width  = QSpinBox()
        self._height = QSpinBox()
        self._format = QComboBox()

        for sb in (self._width, self._height):
            sb.setRange(1, 9999)
            sb.setStyleSheet(_SPINBOX_STYLE)

        self._format.addItems(["ARGB8888", "RGB888", "RGB565", "RGB555"])
        self._format.setStyleSheet(_COMBO_STYLE)

        _field_row(layout, "Width",  self._width)
        _field_row(layout, "Height", self._height)
        _field_row(layout, "Format", self._format)

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._width.valueChanged.connect(self.changed)
        self._height.valueChanged.connect(self.changed)
        self._format.currentIndexChanged.connect(self.changed)

    def load(self, data: dict):
        d = data.get("display", {})
        self._width.setValue(d.get("width", 800))
        self._height.setValue(d.get("height", 480))
        idx = self._format.findText(d.get("format", "ARGB8888"))
        self._format.setCurrentIndex(max(0, idx))

    def save_into(self, data: dict):
        data["display"] = {
            "width":  self._width.value(),
            "height": self._height.value(),
            "format": self._format.currentText(),
        }


class _BootstrapPage(QWidget):
    changed = Signal()

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self._project_root = project_root

        scroll, _, layout = _make_scroll_page()

        _section_header(layout, "Bootstrap", "引擎启动配置（LTDC 双层）")

        # Mode
        self._mode = QComboBox()
        self._mode.addItems(["LTDC"])
        self._mode.setStyleSheet(_COMBO_STYLE)
        _field_row(layout, "Mode", self._mode)

        layout.addSpacing(8)

        # Layer 0
        layer0_lbl = QLabel("Layer 0")
        layer0_lbl.setStyleSheet("color: #aaaaaa; font-size: 12px; letter-spacing: 1px;")
        layout.addWidget(layer0_lbl)
        div0 = QFrame(); div0.setFrameShape(QFrame.HLine)
        div0.setFixedHeight(1); div0.setStyleSheet("background: #333333;")
        layout.addWidget(div0)
        layout.addSpacing(12)

        self._l0_collection, l0_browse = self._make_collection_row()
        self._l0_alpha   = QSpinBox()
        self._l0_alpha.setRange(0, 255); self._l0_alpha.setStyleSheet(_SPINBOX_STYLE)
        self._l0_enabled = QCheckBox("Enabled"); self._l0_enabled.setStyleSheet(_CHECKBOX_STYLE)

        _field_row(layout, "Collection", self._l0_collection, l0_browse)
        _field_row(layout, "Alpha",      self._l0_alpha)
        _field_row(layout, "Enabled",    self._l0_enabled)

        layout.addSpacing(16)

        # Layer 1
        layer1_lbl = QLabel("Layer 1")
        layer1_lbl.setStyleSheet("color: #aaaaaa; font-size: 12px; letter-spacing: 1px;")
        layout.addWidget(layer1_lbl)
        div1 = QFrame(); div1.setFrameShape(QFrame.HLine)
        div1.setFixedHeight(1); div1.setStyleSheet("background: #333333;")
        layout.addWidget(div1)
        layout.addSpacing(12)

        self._l1_collection, l1_browse = self._make_collection_row()
        self._l1_alpha   = QSpinBox()
        self._l1_alpha.setRange(0, 255); self._l1_alpha.setStyleSheet(_SPINBOX_STYLE)
        self._l1_enabled = QCheckBox("Enabled"); self._l1_enabled.setStyleSheet(_CHECKBOX_STYLE)

        _field_row(layout, "Collection", self._l1_collection, l1_browse)
        _field_row(layout, "Alpha",      self._l1_alpha)
        _field_row(layout, "Enabled",    self._l1_enabled)

        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # 信号
        for w in (self._l0_collection, self._l1_collection):
            w.textChanged.connect(self.changed)
        for w in (self._l0_alpha, self._l1_alpha):
            w.valueChanged.connect(self.changed)
        for w in (self._l0_enabled, self._l1_enabled):
            w.stateChanged.connect(self.changed)
        self._mode.currentIndexChanged.connect(self.changed)

    def _make_collection_row(self):
        edit = QLineEdit()
        edit.setStyleSheet(_INPUT_STYLE)
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn = QPushButton("…")
        btn.setFixedSize(32, 28)
        btn.setStyleSheet(_BROWSE_BTN_STYLE)
        btn.clicked.connect(lambda: self._browse_collection(edit))
        return edit, btn

    def _browse_collection(self, edit: QLineEdit):
        start = self._project_root if self._project_root else os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Collection", start, "Collection (*.collection)"
        )
        if path:
            # 转为相对项目根的路径，前缀 /
            if self._project_root:
                try:
                    rel = "/" + os.path.relpath(path, self._project_root).replace(os.sep, "/")
                    path = rel
                except ValueError:
                    pass
            edit.setText(path)

    def load(self, data: dict):
        bs = data.get("bootstrap", {})
        idx = self._mode.findText(bs.get("mode", "LTDC"))
        self._mode.setCurrentIndex(max(0, idx))

        layers = bs.get("layers", [])
        l0 = layers[0] if len(layers) > 0 else {}
        l1 = layers[1] if len(layers) > 1 else {}

        self._l0_collection.setText(l0.get("collection", "/main/Layer0.collection"))
        self._l0_alpha.setValue(l0.get("alpha", 255))
        self._l0_enabled.setChecked(l0.get("enabled", True))

        self._l1_collection.setText(l1.get("collection", "/main/Layer1.collection"))
        self._l1_alpha.setValue(l1.get("alpha", 255))
        self._l1_enabled.setChecked(l1.get("enabled", True))

    def save_into(self, data: dict):
        data["bootstrap"] = {
            "mode": self._mode.currentText(),
            "layers": [
                {
                    "id": 0,
                    "collection": self._l0_collection.text(),
                    "alpha": self._l0_alpha.value(),
                    "enabled": self._l0_enabled.isChecked(),
                },
                {
                    "id": 1,
                    "collection": self._l1_collection.text(),
                    "alpha": self._l1_alpha.value(),
                    "enabled": self._l1_enabled.isChecked(),
                },
            ],
        }


# ── 主编辑器 ──────────────────────────────────

class CartEditor(QWidget):
    """
    .cart 文件可视化编辑器。
    接口与 EditorHost 一致：file_path / modified / save() / modified_changed
    """

    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self._file_path    = file_path
        self._modified     = False
        self._project_root = os.path.dirname(os.path.abspath(file_path))

        self._setup_ui()
        self._load_file()

    # ── 公开 API ──────────────────────────────

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def modified(self) -> bool:
        return self._modified

    def save(self) -> bool:
        try:
            # 读取现有文件，保留未知字段
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

            data["format"]  = "CART_PROJECT"
            data["version"] = 1
            self._project_page.save_into(data)
            self._display_page.save_into(data)
            self._bootstrap_page.save_into(data)

            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            self._set_modified(False)
            return True
        except OSError:
            return False

    # ── UI ────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航
        self._nav = QListWidget()
        self._nav.setFixedWidth(180)
        self._nav.setStyleSheet(_NAV_STYLE)
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self._nav)

        # 右侧内容区
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #1e1e1e;")
        layout.addWidget(self._stack)

        # 创建三个页面
        self._project_page   = _ProjectPage()
        self._display_page   = _DisplayPage()
        self._bootstrap_page = _BootstrapPage(self._project_root)

        for page in (self._project_page, self._display_page, self._bootstrap_page):
            page.changed.connect(lambda: self._set_modified(True))
            self._stack.addWidget(page)

        # 导航条目
        self._add_nav_group("Main")
        self._add_nav_item("Project",   0)
        self._add_nav_item("Display",   1)
        self._add_nav_item("Bootstrap", 2)

        self._nav.setCurrentRow(1)  # 第一个可点击项

    def _add_nav_group(self, text: str):
        item = QListWidgetItem(text.upper())
        item.setFlags(Qt.NoItemFlags)  # 不可选
        self._nav.addItem(item)

    def _add_nav_item(self, text: str, page_index: int):
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, page_index)
        self._nav.addItem(item)

    def _on_nav_changed(self, row: int):
        item = self._nav.item(row)
        if item and item.flags() & Qt.ItemIsEnabled:
            idx = item.data(Qt.UserRole)
            if idx is not None:
                self._stack.setCurrentIndex(idx)

    # ── 数据 ──────────────────────────────────

    def _load_file(self):
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        self._project_page.load(data)
        self._display_page.load(data)
        self._bootstrap_page.load(data)
        self._set_modified(False)

    def _set_modified(self, value: bool):
        if value != self._modified:
            self._modified = value
            self.modified_changed.emit(value)