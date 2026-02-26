"""
CartDark IDE · ui/dialogs/open_project_dialog.py
打开项目对话框：支持选择目录或直接选择 .cart 文件。
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QGroupBox, QRadioButton, QButtonGroup,
    QWidget
)
from PySide6.QtCore import Qt, Signal

from ...state.settings_store import SettingsStore


class OpenProjectDialog(QDialog):
    """打开项目对话框"""

    project_selected = Signal(str)   # 发出项目根目录路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("打开项目")
        self.setMinimumWidth(520)
        self.setMaximumWidth(520)
        self.setSizeGripEnabled(False)

        self._settings = SettingsStore()
        self._setup_ui()
        self._connect_signals()
        self._validate()

    # ── UI ────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 选择方式
        mode_group = QGroupBox("打开方式")
        mode_layout = QVBoxLayout(mode_group)

        self._btn_group = QButtonGroup(self)

        self._radio_dir = QRadioButton("选择项目文件夹")
        self._radio_cart = QRadioButton("选择 .cart 文件")
        self._radio_dir.setChecked(True)

        self._btn_group.addButton(self._radio_dir, 0)
        self._btn_group.addButton(self._radio_cart, 1)

        mode_layout.addWidget(self._radio_dir)
        mode_layout.addWidget(self._radio_cart)
        layout.addWidget(mode_group)

        # 路径输入
        path_group = QGroupBox("路径")
        path_layout = QHBoxLayout(path_group)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择路径…")
        self._path_edit.setReadOnly(True)
        path_layout.addWidget(self._path_edit)

        self._browse_btn = QPushButton("浏览…")
        self._browse_btn.setFixedWidth(72)
        path_layout.addWidget(self._browse_btn)

        layout.addWidget(path_group)

        # 提示标签
        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("color: #e05555; font-size: 12px;")
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

        layout.addStretch()

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("取消")
        btn_layout.addWidget(self._cancel_btn)

        self._open_btn = QPushButton("打开")
        self._open_btn.setEnabled(False)
        self._open_btn.setDefault(True)
        btn_layout.addWidget(self._open_btn)

        layout.addLayout(btn_layout)

    # ── 信号连接 ──────────────────────────────

    def _connect_signals(self):
        self._browse_btn.clicked.connect(self._on_browse)
        self._cancel_btn.clicked.connect(self.reject)
        self._open_btn.clicked.connect(self._on_open)
        self._btn_group.buttonToggled.connect(lambda *_: self._validate())
        self._path_edit.textChanged.connect(self._validate)

    # ── 槽 ────────────────────────────────────

    def _on_browse(self):
        start_dir = self._settings.last_project_location

        if self._radio_dir.isChecked():
            path = QFileDialog.getExistingDirectory(
                self, "选择项目文件夹", start_dir
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择 .cart 文件", start_dir, "CartDark 项目 (*.cart)"
            )

        if path:
            self._path_edit.setText(path)

    def _on_open(self):
        path = self._path_edit.text().strip()
        if not path:
            return

        # 统一转成项目根目录
        if self._radio_cart.isChecked():
            project_root = os.path.dirname(os.path.abspath(path))
        else:
            project_root = os.path.abspath(path)

        # 保存最近路径
        self._settings.last_project_location = os.path.dirname(project_root)

        self.project_selected.emit(project_root)
        self.accept()

    # ── 验证 ──────────────────────────────────

    def _validate(self):
        path = self._path_edit.text().strip()
        ok = False
        hint = ""

        if path:
            if self._radio_dir.isChecked():
                if not os.path.isdir(path):
                    hint = "所选路径不是有效文件夹"
                else:
                    # 检查目录内有没有 .cart 文件
                    has_cart = any(
                        f.endswith(".cart")
                        for f in os.listdir(path)
                        if os.path.isfile(os.path.join(path, f))
                    )
                    if not has_cart:
                        hint = "该文件夹中未找到 .cart 文件"
                    else:
                        ok = True
            else:
                if not os.path.isfile(path):
                    hint = "所选文件不存在"
                elif not path.endswith(".cart"):
                    hint = "请选择 .cart 文件"
                else:
                    ok = True

        self._hint_label.setText(hint)
        self._open_btn.setEnabled(ok)