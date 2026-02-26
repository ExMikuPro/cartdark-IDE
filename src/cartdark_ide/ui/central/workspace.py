"""
CartDark IDE · ui/central/workspace.py
中央工作区：管理标签页 + 编辑器 + 欢迎页。
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt

from .welcome_page import WelcomePage
from ..theme import theme
from .editor_host import EditorHost, make_editor
from ..widgets.tab_header import TabHeader


class Workspace(QWidget):
    """
    中央工作区。

    外部调用：
        workspace.open_file(abs_path)   打开或切换到指定文件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 标签栏（初始隐藏）
        self._tab_bar = TabHeader()
        self._tab_bar.setVisible(False)
        self._tab_bar.tab_activated.connect(self._on_tab_activated)
        self._tab_bar.tab_closed.connect(self._on_tab_close_requested)
        root_layout.addWidget(self._tab_bar)

        # 内容区：欢迎页 + 各编辑器页
        self._stack = QStackedWidget()
        # stack 背景由 _apply_theme 统一设置
        root_layout.addWidget(self._stack)

        # 欢迎页（index 0）
        self._welcome = WelcomePage()
        self._stack.addWidget(self._welcome)

        # 初始化主题（_stack 已创建）
        self._apply_theme()
        theme.changed.connect(lambda _: self._apply_theme())

        # file_path → EditorHost
        self._editors: dict[str, EditorHost] = {}

    # ── 主题 ──────────────────────────────────

    def _apply_theme(self):
        bg = theme.BG_BASE
        self.setStyleSheet(f"background: {bg};")
        self._stack.setStyleSheet(f"background: {bg};")
        # 通知欢迎页
        if hasattr(self, '_welcome') and hasattr(self._welcome, 'apply_theme'):
            self._welcome.apply_theme()

    # ── 公开 API ──────────────────────────────

    def open_file(self, file_path: str, mode: str = "editor"):
        """打开文件：已打开则切换，否则新建标签"""
        if not os.path.isfile(file_path):
            return

        if file_path in self._editors:
            existing_mode = getattr(self._editors[file_path], "_open_mode", "editor")
            if existing_mode == mode:
                self._tab_bar.set_active(file_path)
                self._stack.setCurrentWidget(self._editors[file_path])
                return
            else:
                # mode 不同，关闭后重新以新 mode 打开
                self._close_tab(file_path, confirm=True)
                if file_path in self._editors:
                    return  # 用户取消了关闭确认

        # 新建编辑器：mode=="text" 强制纯文本，否则走工厂函数
        if mode == "text":
            editor = EditorHost(file_path)
        else:
            editor = make_editor(file_path)
        editor._open_mode = mode  # 记录打开模式
        editor.modified_changed.connect(
            lambda mod, fp=file_path: self._on_editor_modified(fp, mod)
        )

        self._editors[file_path] = editor
        self._stack.addWidget(editor)

        title = os.path.basename(file_path)
        self._tab_bar.add_tab(file_path, title)
        self._tab_bar.setVisible(True)
        self._stack.setCurrentWidget(editor)

    def close_file(self, file_path: str):
        """关闭指定文件的标签，不弹确认（文件已被外部删除时调用）"""
        if file_path in self._editors:
            self._close_tab(file_path, confirm=False)

    def save_current(self) -> bool:
        """保存当前激活的文件"""
        tab_id = self._tab_bar.active_id
        if tab_id and tab_id in self._editors:
            return self._editors[tab_id].save()
        return False

    def save_all(self) -> bool:
        """保存所有已修改的文件"""
        ok = True
        for editor in self._editors.values():
            if editor.modified:
                ok = editor.save() and ok
        return ok

    def close_all(self):
        """关闭所有标签（项目关闭时调用）"""
        for fp in list(self._editors.keys()):
            self._close_tab(fp, confirm=False)

    # ── 内部槽 ────────────────────────────────

    def _on_tab_activated(self, tab_id: str):
        if tab_id in self._editors:
            self._stack.setCurrentWidget(self._editors[tab_id])

    def _on_tab_close_requested(self, tab_id: str):
        self._close_tab(tab_id, confirm=True)

    def _on_editor_modified(self, file_path: str, modified: bool):
        self._tab_bar.set_modified(file_path, modified)

    # ── 内部方法 ──────────────────────────────

    def _close_tab(self, file_path: str, confirm: bool):
        editor = self._editors.get(file_path)
        if not editor:
            return

        if confirm and editor.modified:
            name = os.path.basename(file_path)
            choice = self._ask_save(name)
            if choice == "cancel":
                return
            if choice == "save":
                editor.save()

        # 移除
        self._tab_bar.remove_tab(file_path)
        self._stack.removeWidget(editor)
        editor.deleteLater()
        del self._editors[file_path]

    def _ask_save(self, filename: str) -> str:
        """弹出保存确认，返回 'save' / 'discard' / 'cancel'"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

        dlg = QDialog(self)
        dlg.setWindowTitle("未保存的更改")
        dlg.setFixedWidth(380)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        label = QLabel(f'"{filename}" 有未保存的更改，是否保存？')
        label.setWordWrap(True)
        layout.addWidget(label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        discard = QPushButton("不保存")
        cancel  = QPushButton("取消")
        save    = QPushButton("保存")
        save.setDefault(True)
        save.setStyleSheet("""
            QPushButton {
                background: #0a84ff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #339aff; }
            QPushButton:pressed { background: #0060cc; }
        """)

        btn_row.addWidget(discard)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

        result = {"choice": "cancel"}
        discard.clicked.connect(lambda: (result.update(choice="discard"), dlg.accept()))
        cancel.clicked.connect(lambda: (result.update(choice="cancel"),  dlg.reject()))
        save.clicked.connect(lambda: (result.update(choice="save"),    dlg.accept()))

        dlg.exec()
        return result["choice"]

        # 没有标签了，回到欢迎页
        if not self._editors:
            self._tab_bar.setVisible(False)
            self._stack.setCurrentWidget(self._welcome)