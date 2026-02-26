"""
CartDark IDE · ui/central/input_binding_editor.py
.input_binding 文件的可视化编辑器。支持亮/暗主题切换。
"""
from __future__ import annotations

import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QScrollArea,
    QFrame, QHeaderView, QAbstractItemView, QAbstractScrollArea,
    QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QSize

from ..theme import theme


_TOUCH_INPUTS = ["TOUCH_TAP", "TOUCH_DOWN", "TOUCH_UP"]

_GAMEPAD_INPUTS = [
    "PAD_A", "PAD_B", "PAD_X", "PAD_Y",
    "PAD_L1", "PAD_R1",
    "PAD_START", "PAD_SELECT",
    "PAD_UP", "PAD_DOWN", "PAD_LEFT", "PAD_RIGHT",
]


class _PaddedItemDelegate(QStyledItemDelegate):
    """给 ComboBox 下拉列表每一行加高，解决 macOS 下选项过密问题"""
    def sizeHint(self, option, index) -> QSize:
        sh = super().sizeHint(option, index)
        return QSize(sh.width(), max(sh.height(), 32))


def _load_pins(file_path: str) -> list[str]:
    search = os.path.dirname(os.path.abspath(file_path))
    for _ in range(6):
        candidate = os.path.join(search, "board", "pins.json")
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [p["id"] for p in data.get("pins", [])]
            except Exception:
                return []
        parent = os.path.dirname(search)
        if parent == search:
            break
        search = parent
    return []


class _TriggerTable(QWidget):
    changed = Signal()

    def __init__(self, title: str, input_opts: list[str], parent=None):
        super().__init__(parent)
        self._input_opts = input_opts
        self._blocking = False

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 12)
        self._layout.setSpacing(6)

        self._title_lbl = QLabel(title)
        self._layout.addWidget(self._title_lbl)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["输入", "Action"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setColumnWidth(0, 180)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        self._table.setMinimumHeight(40)
        self._table.setMaximumHeight(16777215)
        self._table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self._table.itemChanged.connect(self._on_item_changed)
        self._layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(28, 28)
        self._add_btn.clicked.connect(self._add_row)
        self._del_btn = QPushButton("−")
        self._del_btn.setFixedSize(28, 28)
        self._del_btn.clicked.connect(self._del_row)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._del_btn)
        btn_row.addStretch()
        self._layout.addLayout(btn_row)

        self.apply_theme()

    def apply_theme(self):
        t = theme
        self._title_lbl.setStyleSheet(f"QLabel {{ color: {t.FG_SECONDARY}; font-size: 13px; }}")

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: {t.BG_PANEL};
                border: 1px solid {t.BORDER};
                color: {t.FG_PRIMARY};
                gridline-color: {t.BORDER};
                font-size: 13px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 0px 8px;
            }}
            QTableWidget::item:selected {{
                background: {t.BG_SELECTED};
                color: {t.FG_TITLE};
            }}
            QHeaderView::section {{
                background: {t.BG_HEADER};
                color: {t.FG_SECONDARY};
                border: none;
                border-bottom: 1px solid {t.BORDER};
                border-right: 1px solid {t.BORDER};
                padding: 4px 8px;
                font-size: 12px;
            }}
            QHeaderView::section:last {{ border-right: none; }}
        """)

        btn_style = f"""
            QPushButton {{
                background: {t.BTN_BG};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {t.BTN_HOVER}; }}
            QPushButton:pressed {{ background: {t.BTN_PRESSED}; }}
        """
        self._add_btn.setStyleSheet(btn_style)
        self._del_btn.setStyleSheet(btn_style)

        combo_style = self._combo_style()
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, 0)
            if combo:
                combo.setStyleSheet(combo_style)

    def _combo_style(self) -> str:
        t = theme
        return f"""
            QComboBox {{
                background: {t.BG_WIDGET};
                color: {t.FG_PRIMARY};
                border: none;
                padding: 2px 24px 2px 8px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                border: none;
                background: transparent;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 8px;
                height: 8px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {t.ARROW};
            }}
            QComboBox QAbstractItemView {{
                background: {t.BG_WIDGET};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                selection-background-color: {t.BG_SELECTED};
                selection-color: {t.FG_TITLE};
                outline: none;
                padding: 4px 0;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 14px;
                min-height: 28px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {t.BG_HOVER};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {t.BG_SELECTED};
                color: {t.FG_TITLE};
            }}
        """

    def load_rows(self, rows: list[dict]):
        self._blocking = True
        self._table.setRowCount(0)
        for row in rows:
            self._append_row(row.get("input", ""), row.get("action", ""))
        self._blocking = False
        self._adjust_height()

    def get_rows(self) -> list[dict]:
        result = []
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, 0)
            item  = self._table.item(r, 1)
            result.append({
                "input":  combo.currentText() if combo else "",
                "action": item.text()          if item  else "",
                "event":  "press",
            })
        return result

    def update_input_opts(self, opts: list[str]):
        self._input_opts = opts
        combo_style = self._combo_style()
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, 0)
            if combo:
                cur = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(opts)
                idx = combo.findText(cur)
                combo.setCurrentIndex(max(0, idx))
                combo.setStyleSheet(combo_style)
                combo.blockSignals(False)

    def _append_row(self, inp: str = "", action: str = ""):
        self._blocking = True
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setRowHeight(r, 36)

        combo = QComboBox()
        combo.addItems(self._input_opts)
        combo.setEditable(False)
        combo.setStyleSheet(self._combo_style())
        combo.view().setItemDelegate(_PaddedItemDelegate(combo))
        idx = combo.findText(inp)
        combo.setCurrentIndex(max(0, idx))
        combo.currentIndexChanged.connect(lambda _: self.changed.emit())
        self._table.setCellWidget(r, 0, combo)

        item = QTableWidgetItem(action)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        self._table.setItem(r, 1, item)

        self._blocking = False
        self._adjust_height()

    def _add_row(self):
        default = self._input_opts[0] if self._input_opts else ""
        self._append_row(default, "")
        self.changed.emit()

    def _del_row(self):
        row = self._table.currentRow()
        if row < 0:
            row = self._table.rowCount() - 1
        if row >= 0:
            self._table.removeRow(row)
            self._adjust_height()
            self.changed.emit()

    def _on_item_changed(self, item):
        if not self._blocking:
            self.changed.emit()

    def _adjust_height(self):
        header_h = self._table.horizontalHeader().height()
        rows = self._table.rowCount()
        row_h = sum(self._table.rowHeight(r) for r in range(rows)) if rows else 36
        self._table.setFixedHeight(max(40, header_h + row_h + 2))


class InputBindingEditor(QWidget):
    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._modified  = False
        self._pins      = _load_pins(file_path)

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
            data = self._build_data()
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            self._set_modified(False)
            return True
        except OSError:
            return False

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(self._scroll)

        self._content = QWidget()
        self._scroll.setWidget(self._content)

        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        self._title_lbl = QLabel("输入绑定")
        self._title_lbl.setStyleSheet(f"color: {theme.FG_TITLE}; font-size: 20px; font-weight: bold;")
        layout.addWidget(self._title_lbl)

        self._pin_table     = _TriggerTable("引脚输入",     self._pins)
        self._touch_table   = _TriggerTable("触摸输入",   _TOUCH_INPUTS)
        self._gamepad_table = _TriggerTable("游戏手柄输入", _GAMEPAD_INPUTS)

        for tbl in (self._pin_table, self._touch_table, self._gamepad_table):
            tbl.changed.connect(lambda: self._set_modified(True))
            layout.addWidget(tbl)

        layout.addStretch()
        self._apply_bg()

    def _apply_bg(self):
        t = theme
        self._scroll.setStyleSheet(f"background: {t.BG_BASE}; border: none;")
        self._content.setStyleSheet(f"background: {t.BG_BASE};")
        self._title_lbl.setStyleSheet(f"QLabel {{ color: {t.FG_TITLE}; font-size: 20px; font-weight: bold; }}")

    def _on_theme_changed(self, _name: str):
        self._apply_bg()
        for tbl in (self._pin_table, self._touch_table, self._gamepad_table):
            tbl.apply_theme()

    def _load_file(self):
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        self._pin_table.load_rows(data.get("pin_triggers", []))
        self._touch_table.load_rows(data.get("touch_triggers", []))
        self._gamepad_table.load_rows(data.get("gamepad_triggers", []))
        self._set_modified(False)

    def _build_data(self) -> dict:
        return {
            "format":           "CART_INPUT_BINDING",
            "version":          1,
            "name":             os.path.splitext(os.path.basename(self._file_path))[0],
            "pin_triggers":     self._pin_table.get_rows(),
            "touch_triggers":   self._touch_table.get_rows(),
            "gamepad_triggers": self._gamepad_table.get_rows(),
        }

    def _set_modified(self, value: bool):
        if value != self._modified:
            self._modified = value
            self.modified_changed.emit(value)