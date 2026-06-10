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

from ..project.schema import CART_PROJECT_FORMAT, CartValidationError, validate_cart_data
from ..ui.theme import theme


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

        self._header_title = QLabel("Project")
        self._subtitle     = QLabel("工程基本信息")
        self._div          = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._header_title, self._subtitle, self._div)

        self._title     = QLineEdit()
        self._title_zh  = QLineEdit()
        self._version   = QLineEdit()
        self._developer = QLineEdit()
        self._min_fw    = QLineEdit()
        self._id        = QLineEdit(); self._id.setReadOnly(True)

        self._lbl_title     = QLabel("应用名称")
        self._lbl_title_zh  = QLabel("中文名称")
        self._lbl_version   = QLabel("版本")
        self._lbl_developer = QLabel("开发者")
        self._lbl_min_fw    = QLabel("最小固件版本")
        self._lbl_id        = QLabel("ID")

        _field_row(layout, self._lbl_title,     self._title)
        _field_row(layout, self._lbl_title_zh,  self._title_zh)
        _field_row(layout, self._lbl_version,   self._version)
        _field_row(layout, self._lbl_developer, self._developer)
        _field_row(layout, self._lbl_min_fw,    self._min_fw)
        _field_row(layout, self._lbl_id,        self._id)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        for w in (self._title, self._title_zh, self._version,
                  self._developer, self._min_fw):
            w.textChanged.connect(self.changed)
        self.apply_theme()

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._header_title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")
        for lbl in (self._lbl_title, self._lbl_title_zh, self._lbl_version,
                    self._lbl_developer, self._lbl_min_fw, self._lbl_id):
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
        for w in (self._title, self._title_zh, self._version,
                  self._developer, self._min_fw):
            w.setStyleSheet(input_style)
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
        return

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
        self._title.setText(p.get("title", p.get("name", "")))
        self._title_zh.setText(p.get("title_zh", ""))
        self._version.setText(p.get("version", "0.1.0"))
        self._developer.setText(p.get("developer", ""))
        self._min_fw.setText(p.get("min_fw", "0.1.0"))
        self._id.setText(p.get("id", ""))

    def save_into(self, data: dict):
        data.setdefault("project", {})
        current_id = data["project"].get("id") or self._id.text()
        data["project"] = {
            "id": current_id,
            "title": self._title.text(),
            "title_zh": self._title_zh.text(),
            "version": self._version.text(),
            "developer": self._developer.text(),
            "min_fw": self._min_fw.text(),
        }


class _PlatformsPage(QWidget):
    changed = Signal()

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self._project_root = project_root
        self._scroll, self._content, layout = _make_scroll_page()

        self._header_title = QLabel("Platforms")
        self._subtitle     = QLabel("平台相关配置")
        self._div          = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._header_title, self._subtitle, self._div)

        self._app_icon, self._app_icon_browse = self._make_path_row("Image (*.png *.jpg *.jpeg *.bmp)")
        self._lbl_app_icon = QLabel("CartDark OS 图标")

        _field_row(layout, self._lbl_app_icon, self._app_icon, self._app_icon_browse)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._app_icon.textChanged.connect(self.changed)
        self.apply_theme()

    def _make_path_row(self, file_filter: str):
        edit = QLineEdit()
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn = QPushButton("…")
        btn.setFixedSize(32, 28)
        btn.clicked.connect(lambda: self._browse_path(edit, file_filter))
        return edit, btn

    def _browse_path(self, edit: QLineEdit, file_filter: str):
        start = self._project_root or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", start, file_filter)
        if path and self._project_root:
            try:
                path = os.path.relpath(path, self._project_root).replace(os.sep, "/")
            except ValueError:
                pass
        if path:
            edit.setText(path)

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._header_title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")
        self._lbl_app_icon.setStyleSheet(f"color: {t.FG_SECONDARY}; font-size: 13px;")
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
        self._app_icon.setStyleSheet(input_style)
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
        self._app_icon_browse.setStyleSheet(browse_style)

    def load(self, data: dict):
        platforms = data.get("platforms", {})
        cartdark_os = platforms.get("cartdark-os", {})
        self._app_icon.setText(cartdark_os.get("app_icon", "assets/app_icon.png"))

    def save_into(self, data: dict):
        data["platforms"] = {
            "cartdark-os": {
                "app_icon": self._app_icon.text(),
            }
        }


class _DisplayPage(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll, self._content, layout = _make_scroll_page()

        self._header_title = QLabel("Display")
        self._subtitle     = QLabel("目标屏幕尺寸")
        self._div          = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._header_title, self._subtitle, self._div)

        self._width = QSpinBox()
        self._height = QSpinBox()
        for spin in (self._width, self._height):
            spin.setRange(1, 100000)
            spin.setSingleStep(1)

        self._lbl_width = QLabel("宽度")
        self._lbl_height = QLabel("高度")
        _field_row(layout, self._lbl_width, self._width)
        _field_row(layout, self._lbl_height, self._height)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._width.valueChanged.connect(self.changed)
        self._height.valueChanged.connect(self.changed)
        self.apply_theme()

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._header_title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")
        for lbl in (self._lbl_width, self._lbl_height):
            lbl.setStyleSheet(f"color: {t.FG_SECONDARY}; font-size: 13px;")
        input_style = f"""
            QSpinBox {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QSpinBox:focus {{ border-color: {t.BORDER_FOCUS}; }}
        """
        for spin in (self._width, self._height):
            spin.setStyleSheet(input_style)

    def load(self, data: dict):
        display = data.get("display", {})
        width = display.get("width", 800)
        height = display.get("height", 480)
        self._width.setValue(width if isinstance(width, int) and width > 0 else 800)
        self._height.setValue(height if isinstance(height, int) and height > 0 else 480)

    def save_into(self, data: dict):
        data["display"] = {
            "width": self._width.value(),
            "height": self._height.value(),
        }


class _BootstrapPage(QWidget):
    changed = Signal()

    def __init__(self, project_root: str, parent=None):
        super().__init__(parent)
        self._project_root = project_root

        self._scroll, self._content, layout = _make_scroll_page()

        self._header_title = QLabel("Bootstrap")
        self._subtitle     = QLabel("启动入口（Lua 与 LTDC layer）")
        self._div          = QFrame(); self._div.setFrameShape(QFrame.HLine); self._div.setFixedHeight(1)
        _section_header(layout, self._header_title, self._subtitle, self._div)

        self._entry, self._entry_browse = self._make_path_row("Lua (*.lua)")
        self._layer0, self._layer0_browse = self._make_path_row("Layer (*.layer)")
        self._layer1, self._layer1_browse = self._make_path_row("Layer (*.layer)")

        self._lbl_entry = QLabel("Lua 入口")
        self._lbl_layer0 = QLabel("Layer 0")
        self._lbl_layer1 = QLabel("Layer 1")

        _field_row(layout, self._lbl_entry, self._entry, self._entry_browse)
        _field_row(layout, self._lbl_layer0, self._layer0, self._layer0_browse)
        _field_row(layout, self._lbl_layer1, self._layer1, self._layer1_browse)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        for w in (self._entry, self._layer0, self._layer1):
            w.textChanged.connect(self.changed)

        self.apply_theme()

    def _make_path_row(self, file_filter: str):
        edit = QLineEdit()
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn = QPushButton("…")
        btn.setFixedSize(32, 28)
        btn.clicked.connect(lambda: self._browse_path(edit, file_filter))
        return edit, btn

    def _browse_path(self, edit: QLineEdit, file_filter: str):
        start = self._project_root or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", start, file_filter)
        if path and self._project_root:
            try:
                path = os.path.relpath(path, self._project_root).replace(os.sep, "/")
            except ValueError:
                pass
        if path:
            edit.setText(path)

    def apply_theme(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._header_title.setStyleSheet(f"color: {t.FG_TITLE}; font-size: 18px; font-weight: bold;")
        self._subtitle.setStyleSheet(f"color: {t.SECTION_SUB}; font-size: 12px; margin-top: 2px;")
        self._div.setStyleSheet(f"background: {t.DIVIDER};")

        for lbl in (self._lbl_entry, self._lbl_layer0, self._lbl_layer1):
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
        for w in (self._entry, self._layer0, self._layer1):
            w.setStyleSheet(input_style)

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
        for btn in (self._entry_browse, self._layer0_browse, self._layer1_browse):
            btn.setStyleSheet(browse_style)

    def load(self, data: dict):
        bs = data.get("bootstrap", {})
        self._entry.setText(bs.get("entry", "scripts/main.lua"))
        self._layer0.setText(bs.get("layer0", ""))
        self._layer1.setText(bs.get("layer1", "layers/default.layer"))

    def save_into(self, data: dict):
        data["bootstrap"] = {
            "entry": self._entry.text(),
            "layer0": self._layer0.text(),
            "layer1": self._layer1.text(),
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
                    current_data = json.load(f)
            except Exception:
                current_data = {}
            data = {"format": CART_PROJECT_FORMAT}
            current_id = ""
            if isinstance(current_data, dict) and isinstance(current_data.get("project"), dict):
                current_id = current_data["project"].get("id", "")
            self._bootstrap_page.save_into(data)
            data["project"] = {"id": current_id}
            self._project_page.save_into(data)
            self._platforms_page.save_into(data)
            self._display_page.save_into(data)
            validate_cart_data(data, self._project_root)
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            self._set_modified(False)
            return True
        except (OSError, CartValidationError):
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
        self._platforms_page = _PlatformsPage(self._project_root)
        self._bootstrap_page = _BootstrapPage(self._project_root)
        self._display_page = _DisplayPage()

        for page in (
            self._project_page, self._platforms_page,
            self._bootstrap_page, self._display_page
        ):
            page.changed.connect(lambda: self._set_modified(True))
            self._stack.addWidget(page)

        self._add_nav_group("Main")
        self._add_nav_item("Project",   0)
        self._add_nav_item("Platforms", 1)
        self._add_nav_item("Bootstrap", 2)
        self._add_nav_item("Display",   3)

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
        for page in (
            self._project_page, self._platforms_page,
            self._bootstrap_page, self._display_page
        ):
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
        self._platforms_page.load(data)
        self._bootstrap_page.load(data)
        self._display_page.load(data)
        self._set_modified(False)

    def _set_modified(self, value: bool):
        if value != self._modified:
            self._modified = value
            self.modified_changed.emit(value)
