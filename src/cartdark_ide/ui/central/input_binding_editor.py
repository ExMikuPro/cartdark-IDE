"""
CartDark IDE · ui/central/input_binding_editor.py
.input_binding 文件的可视化编辑器。

三个表格区域：
  - Pin Triggers     (Input = 下拉框，从 board/pins.json 读取)
  - Touch Triggers   (Input = 下拉框，固定选项)
  - Gamepad Triggers (Input = 下拉框，固定选项)

每个表格列：Input | Action
"""
from __future__ import annotations

import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QScrollArea,
    QFrame, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal


# ── 固定选项 ──────────────────────────────────

_TOUCH_INPUTS = ["TOUCH_TAP", "TOUCH_DOWN", "TOUCH_UP"]

_GAMEPAD_INPUTS = [
    "PAD_A", "PAD_B", "PAD_X", "PAD_Y",
    "PAD_L1", "PAD_R1",
    "PAD_START", "PAD_SELECT",
    "PAD_UP", "PAD_DOWN", "PAD_LEFT", "PAD_RIGHT",
]

_COMBO_STYLE = """
QComboBox {
    background: #2d2d2d;
    color: #cccccc;
    border: none;
    padding: 2px 6px;
    font-size: 13px;
}
QComboBox::drop-down {
    border: none;
    background: #2d2d2d;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #888888;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background: #2d2d2d;
    color: #cccccc;
    border: 1px solid #555;
    selection-background-color: #094771;
    outline: none;
}
"""

_TABLE_STYLE = """
QTableWidget {
    background: #252526;
    border: 1px solid #3c3c3c;
    color: #cccccc;
    gridline-color: #3c3c3c;
    font-size: 13px;
    outline: none;
}
QTableWidget::item {
    padding: 0px 8px;
}
QTableWidget::item:selected {
    background: #094771;
    color: #ffffff;
}
QHeaderView::section {
    background: #2d2d2d;
    color: #888888;
    border: none;
    border-bottom: 1px solid #3c3c3c;
    border-right: 1px solid #3c3c3c;
    padding: 4px 8px;
    font-size: 12px;
}
QHeaderView::section:last {
    border-right: none;
}
"""

_BTN_STYLE = """
QPushButton {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555;
    border-radius: 4px;
    font-size: 16px;
    font-weight: bold;
}
QPushButton:hover { background: #4e4e4e; }
QPushButton:pressed { background: #2a2a2a; }
"""


# ── 找 board/pins.json ────────────────────────

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


# ── 单个 Trigger 表格 ─────────────────────────

class _TriggerTable(QWidget):
    changed = Signal()

    def __init__(self, title: str, input_opts: list[str], parent=None):
        super().__init__(parent)
        self._input_opts = input_opts
        self._blocking = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(6)

        # 标题
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #aaaaaa; font-size: 13px;")
        layout.addWidget(lbl)

        # 表格：只有 Input | Action 两列
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Input", "Action"])
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
        self._table.setMaximumHeight(16777215)  # 不限制最大高度
        from PySide6.QtWidgets import QAbstractScrollArea
        self._table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._table.setStyleSheet(_TABLE_STYLE)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        # +/- 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setStyleSheet(_BTN_STYLE)
        add_btn.clicked.connect(self._add_row)
        del_btn = QPushButton("−")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet(_BTN_STYLE)
        del_btn.clicked.connect(self._del_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ── 公开 ──────────────────────────────────

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
                "event":  "press",             # v1 默认 press
            })
        return result

    def update_input_opts(self, opts: list[str]):
        self._input_opts = opts
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, 0)
            if combo:
                cur = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(opts)
                idx = combo.findText(cur)
                combo.setCurrentIndex(max(0, idx))
                combo.blockSignals(False)

    # ── 内部 ──────────────────────────────────

    def _append_row(self, inp: str = "", action: str = ""):
        self._blocking = True
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setRowHeight(r, 28)

        combo = QComboBox()
        combo.addItems(self._input_opts)
        combo.setEditable(False)
        combo.setStyleSheet(_COMBO_STYLE)
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
        """根据行数自动调整表格高度"""
        header_h = self._table.horizontalHeader().height()
        rows = self._table.rowCount()
        if rows == 0:
            row_h = 28
        else:
            row_h = sum(self._table.rowHeight(r) for r in range(rows))
        total = header_h + row_h + 2  # +2 for border
        self._table.setFixedHeight(max(40, total))


# ── 主编辑器 ──────────────────────────────────

class InputBindingEditor(QWidget):
    """
    .input_binding 可视化编辑器。
    接口与 EditorHost 一致：file_path / modified / save() / modified_changed
    """

    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._modified  = False
        self._pins      = _load_pins(file_path)

        self._setup_ui()
        self._load_file()

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

    # ── UI ────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: #1e1e1e; border: none;")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: #1e1e1e;")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("Input Bindings")
        title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self._pin_table     = _TriggerTable("Pin Triggers",     self._pins)
        self._touch_table   = _TriggerTable("Touch Triggers",   _TOUCH_INPUTS)
        self._gamepad_table = _TriggerTable("Gamepad Triggers", _GAMEPAD_INPUTS)

        for tbl in (self._pin_table, self._touch_table, self._gamepad_table):
            tbl.changed.connect(lambda: self._set_modified(True))
            layout.addWidget(tbl)

        layout.addStretch()

    # ── 数据 ──────────────────────────────────

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