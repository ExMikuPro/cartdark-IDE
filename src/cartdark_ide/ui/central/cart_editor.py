"""
CartDark IDE · ui/central/cart_editor.py
.cart 工程文件的可视化编辑器。支持亮/暗主题切换。
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

from ..theme import theme


def _make_scroll_page() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(32, 24, 32, 32)
    layout.setSpacing(0)
    scroll.setWidget(content)
    return scroll, content, layout


def _section_header(layout: QVBoxLayout, title_lbl: QLabel,
                    sub_lbl: QLabel | None, div: QFrame):
    layout.addWidget(title_lbl)
    if sub_lbl:
        layout.addWidget(sub_lbl)
    layout.addSpacing(12)
    layout.addWidget(div)
    layout.addSpacing(20)


def _field_row(layout: QVBoxLayout, label_widget: QLabel,
               widget: QWidget, extra: QWidget = None):
    row = QHBoxLayout()
    row.setSpacing(12)
    label_widget.setFixedWidth(180)
    label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    row.addWidget(label_widget)
    row.addWidget(widget)
    if extra:
        row.addWidget(extra)
    row.addStretch()
    layout.addLayout(row)
    layout.addSpacing(14)


class _ProjectPage(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll, self._content, layout = _make_scroll_page()

        self._title     = QLabel("Project")
        self._subtitle  = QLabel("工程基本信息")
        self._div       = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._title, self._subtitle, self._div)

        self._name     = QLineEdit()
        self._id       = QLineEdit(); self._id.setReadOnly(True)
        self._template = QComboBox()
        self._template.addItems(["blank", "cartdark_os"])

        self._lbl_name     = QLabel("Name")
        self._lbl_template = QLabel("Template")
        self._lbl_id       = QLabel("ID")

        _field_row(layout, self._lbl_name,     self._name)
        _field_row(layout, self._lbl_template, self._template)
        _field_row(layout, self._lbl_id,       self._id)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._name.textChanged.connect(self.changed)
        self._template.currentIndexChanged.connect(self.changed)
        self.apply_theme()

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")
        for lbl in (self._lbl_name, self._lbl_template, self._lbl_id):
            lbl.setStyleSheet(f"color: {t.FG_SECONDARY}; font-size: 13px;")
        input_style = f"""
            QLineEdit {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {t.BORDER_FOCUS}; }}
        """
        self._name.setStyleSheet(input_style)
        self._id.setStyleSheet(f"""
            QLineEdit {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_READONLY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
            }}
        """)
        self._template.setStyleSheet(self._combo_style())

    def _combo_style(self) -> str:
        t = theme
        return f"""
            QComboBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{ border: none; background: {t.BG_WIDGET_ALT}; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {t.ARROW};
                width: 0; height: 0;
            }}
            QComboBox QAbstractItemView {{
                background: {t.BG_WIDGET};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                selection-background-color: {t.BG_SELECTED};
                outline: none;
            }}
        """

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


class _DisplayPage(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll, self._content, layout = _make_scroll_page()

        self._title    = QLabel("Display")
        self._subtitle = QLabel("显示参数")
        self._div      = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._title, self._subtitle, self._div)

        self._width  = QSpinBox(); self._width.setRange(1, 9999)
        self._height = QSpinBox(); self._height.setRange(1, 9999)
        self._format = QComboBox()
        self._format.addItems(["ARGB8888", "RGB888", "RGB565", "RGB555"])

        self._lbl_w = QLabel("Width")
        self._lbl_h = QLabel("Height")
        self._lbl_f = QLabel("Format")

        _field_row(layout, self._lbl_w, self._width)
        _field_row(layout, self._lbl_h, self._height)
        _field_row(layout, self._lbl_f, self._format)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._width.valueChanged.connect(self.changed)
        self._height.valueChanged.connect(self.changed)
        self._format.currentIndexChanged.connect(self.changed)
        self.apply_theme()

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")
        for lbl in (self._lbl_w, self._lbl_h, self._lbl_f):
            lbl.setStyleSheet(f"color: {t.FG_SECONDARY}; font-size: 13px;")
        spinbox_style = f"""
            QSpinBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 80px;
            }}
            QSpinBox:focus {{ border-color: {t.BORDER_FOCUS}; }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px; background: {t.BG_HOVER}; border: none;
            }}
        """
        self._width.setStyleSheet(spinbox_style)
        self._height.setStyleSheet(spinbox_style)
        self._format.setStyleSheet(f"""
            QComboBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{ border: none; background: {t.BG_WIDGET_ALT}; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {t.ARROW};
                width: 0; height: 0;
            }}
            QComboBox QAbstractItemView {{
                background: {t.BG_WIDGET};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                selection-background-color: {t.BG_SELECTED};
                outline: none;
            }}
        """)

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

        self._scroll, self._content, layout = _make_scroll_page()

        self._title    = QLabel("Bootstrap")
        self._subtitle = QLabel("引擎启动配置（LTDC 双层）")
        self._div      = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._title, self._subtitle, self._div)

        self._lbl_mode = QLabel("Mode")
        self._mode = QComboBox(); self._mode.addItems(["LTDC"])
        _field_row(layout, self._lbl_mode, self._mode)
        layout.addSpacing(8)

        # Layer 0
        self._lyr0_lbl  = QLabel("Layer 0")
        self._lyr0_div  = QFrame(); self._lyr0_div.setFrameShape(QFrame.HLine); self._lyr0_div.setFixedHeight(1)
        layout.addWidget(self._lyr0_lbl)
        layout.addWidget(self._lyr0_div)
        layout.addSpacing(12)

        self._l0_col, self._l0_browse = self._make_collection_row()
        self._l0_alpha   = QSpinBox(); self._l0_alpha.setRange(0, 255)
        self._l0_enabled = QCheckBox("Enabled")
        self._lbl_l0c = QLabel("Collection"); self._lbl_l0a = QLabel("Alpha"); self._lbl_l0e = QLabel("Enabled")
        _field_row(layout, self._lbl_l0c, self._l0_col, self._l0_browse)
        _field_row(layout, self._lbl_l0a, self._l0_alpha)
        _field_row(layout, self._lbl_l0e, self._l0_enabled)
        layout.addSpacing(16)

        # Layer 1
        self._lyr1_lbl  = QLabel("Layer 1")
        self._lyr1_div  = QFrame(); self._lyr1_div.setFrameShape(QFrame.HLine); self._lyr1_div.setFixedHeight(1)
        layout.addWidget(self._lyr1_lbl)
        layout.addWidget(self._lyr1_div)
        layout.addSpacing(12)

        self._l1_col, self._l1_browse = self._make_collection_row()
        self._l1_alpha   = QSpinBox(); self._l1_alpha.setRange(0, 255)
        self._l1_enabled = QCheckBox("Enabled")
        self._lbl_l1c = QLabel("Collection"); self._lbl_l1a = QLabel("Alpha"); self._lbl_l1e = QLabel("Enabled")
        _field_row(layout, self._lbl_l1c, self._l1_col, self._l1_browse)
        _field_row(layout, self._lbl_l1a, self._l1_alpha)
        _field_row(layout, self._lbl_l1e, self._l1_enabled)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        for w in (self._l0_col, self._l1_col):
            w.textChanged.connect(self.changed)
        for w in (self._l0_alpha, self._l1_alpha):
            w.valueChanged.connect(self.changed)
        for w in (self._l0_enabled, self._l1_enabled):
            w.stateChanged.connect(self.changed)
        self._mode.currentIndexChanged.connect(self.changed)

        self.apply_theme()

    def _make_collection_row(self):
        edit = QLineEdit()
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn = QPushButton("…")
        btn.setFixedSize(32, 28)
        btn.clicked.connect(lambda: self._browse_collection(edit))
        return edit, btn

    def _browse_collection(self, edit: QLineEdit):
        start = self._project_root or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Collection", start, "Collection (*.collection)"
        )
        if path and self._project_root:
            try:
                path = "/" + os.path.relpath(path, self._project_root).replace(os.sep, "/")
            except ValueError:
                pass
        if path:
            edit.setText(path)

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")

        for lbl in (self._lyr0_lbl, self._lyr1_lbl):
            lbl.setStyleSheet(f"color: {t.FG_SECONDARY}; font-size: 12px; letter-spacing: 1px;")
        for d in (self._lyr0_div, self._lyr1_div):
            d.setStyleSheet(f"background: {t.DIVIDER_LIGHT};")

        field_lbl_style = f"color: {t.FG_SECONDARY}; font-size: 13px;"
        for lbl in (self._lbl_mode, self._lbl_l0c, self._lbl_l0a, self._lbl_l0e,
                    self._lbl_l1c, self._lbl_l1a, self._lbl_l1e):
            lbl.setStyleSheet(field_lbl_style)

        input_style = f"""
            QLineEdit {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {t.BORDER_FOCUS}; }}
        """
        self._l0_col.setStyleSheet(input_style)
        self._l1_col.setStyleSheet(input_style)

        spinbox_style = f"""
            QSpinBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 80px;
            }}
            QSpinBox:focus {{ border-color: {t.BORDER_FOCUS}; }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px; background: {t.BG_HOVER}; border: none;
            }}
        """
        self._l0_alpha.setStyleSheet(spinbox_style)
        self._l1_alpha.setStyleSheet(spinbox_style)

        checkbox_style = f"""
            QCheckBox {{ color: {t.FG_PRIMARY}; font-size: 13px; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                background: {t.BG_WIDGET_ALT};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {t.ACCENT};
                border-color: {t.ACCENT};
            }}
        """
        self._l0_enabled.setStyleSheet(checkbox_style)
        self._l1_enabled.setStyleSheet(checkbox_style)

        browse_style = f"""
            QPushButton {{
                background: {t.BTN_BG};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {t.BTN_HOVER}; }}
            QPushButton:pressed {{ background: {t.BTN_PRESSED}; }}
        """
        self._l0_browse.setStyleSheet(browse_style)
        self._l1_browse.setStyleSheet(browse_style)

        combo_style = f"""
            QComboBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{ border: none; background: {t.BG_WIDGET_ALT}; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {t.ARROW};
                width: 0; height: 0;
            }}
            QComboBox QAbstractItemView {{
                background: {t.BG_WIDGET};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                selection-background-color: {t.BG_SELECTED};
                outline: none;
            }}
        """
        self._mode.setStyleSheet(combo_style)

    def load(self, data: dict):
        bs = data.get("bootstrap", {})
        idx = self._mode.findText(bs.get("mode", "LTDC"))
        self._mode.setCurrentIndex(max(0, idx))
        layers = bs.get("layers", [])
        l0 = layers[0] if len(layers) > 0 else {}
        l1 = layers[1] if len(layers) > 1 else {}
        self._l0_col.setText(l0.get("collection", "/main/Layer0.collection"))
        self._l0_alpha.setValue(l0.get("alpha", 255))
        self._l0_enabled.setChecked(l0.get("enabled", True))
        self._l1_col.setText(l1.get("collection", "/main/Layer1.collection"))
        self._l1_alpha.setValue(l1.get("alpha", 255))
        self._l1_enabled.setChecked(l1.get("enabled", True))

    def save_into(self, data: dict):
        data["bootstrap"] = {
            "mode": self._mode.currentText(),
            "layers": [
                {"id": 0, "collection": self._l0_col.text(),
                 "alpha": self._l0_alpha.value(), "enabled": self._l0_enabled.isChecked()},
                {"id": 1, "collection": self._l1_col.text(),
                 "alpha": self._l1_alpha.value(), "enabled": self._l1_enabled.isChecked()},
            ],
        }


class CartEditor(QWidget):
    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self._file_path    = file_path
        self._modified     = False
        self._project_root = os.path.dirname(os.path.abspath(file_path))

        self._setup_ui()
        self._load_file()
        theme.changed.connect(self._on_theme_changed)

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def modified(self) -> bool:
        return self._modified

    def save(self) -> bool:
        try:
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

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setFixedWidth(180)
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self._nav)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._project_page   = _ProjectPage()
        self._display_page   = _DisplayPage()
        self._bootstrap_page = _BootstrapPage(self._project_root)

        for page in (self._project_page, self._display_page, self._bootstrap_page):
            page.changed.connect(lambda: self._set_modified(True))
            self._stack.addWidget(page)

        self._add_nav_group("Main")
        self._add_nav_item("Project",   0)
        self._add_nav_item("Display",   1)
        self._add_nav_item("Bootstrap", 2)

        self._nav.setCurrentRow(1)
        self._apply_nav_theme()

    def _apply_nav_theme(self):
        t = theme
        self._nav.setStyleSheet(f"""
            QListWidget {{
                background: {t.BG_NAV};
                border: none;
                border-right: 1px solid {t.BORDER};
                outline: none;
                padding: 8px 0;
            }}
            QListWidget::item {{
                color: {t.FG_SECONDARY};
                padding: 6px 20px;
                font-size: 13px;
            }}
            QListWidget::item:selected {{
                background: {t.BG_NAV_ACTIVE};
                color: {t.FG_PRIMARY};
            }}
            QListWidget::item:hover:!selected {{
                background: {t.BG_NAV_HOVER};
                color: {t.FG_PRIMARY};
            }}
            QListWidget::item:disabled {{
                color: {t.NAV_GROUP};
                padding: 12px 20px 4px 20px;
                font-size: 11px;
                letter-spacing: 1px;
            }}
        """)
        self._stack.setStyleSheet(f"background: {t.BG_BASE};")

    def _on_theme_changed(self, _name: str):
        self._apply_nav_theme()
        for page in (self._project_page, self._display_page, self._bootstrap_page):
            page.apply_theme()

    def _add_nav_group(self, text: str):
        item = QListWidgetItem(text.upper())
        item.setFlags(Qt.NoItemFlags)
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