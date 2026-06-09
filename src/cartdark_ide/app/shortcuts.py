"""
CartDark IDE · ui/shortcuts.py
全局快捷键注册。

所有快捷键集中在此文件定义，便于查阅和修改。
register_shortcuts(window) 在 MainWindow.__init__ 末尾调用。
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt


def register_shortcuts(window) -> None:
    """向 MainWindow 注册所有全局快捷键"""

    ws = window.workspace  # Workspace

    # ── 文件 ──────────────────────────────────────

    # ⌘S / Ctrl+S  保存当前文件
    _bind(window, "Ctrl+S", lambda: ws.save_current())

    # ⌘Shift+S / Ctrl+Shift+S  全部保存
    _bind(window, "Ctrl+Shift+S", lambda: ws.save_all())

    # ⌘W / Ctrl+W  关闭当前标签
    _bind(window, "Ctrl+W", lambda: ws.close_current_tab())

    # ⌘Shift+T / Ctrl+Shift+T  重新打开最近关闭的文件
    _bind(window, "Ctrl+Shift+T", lambda: ws.reopen_last_closed())

    # ── 项目 ──────────────────────────────────────

    # ⌘N / Ctrl+N  新建项目
    _bind(window, "Ctrl+N", lambda: window.open_new_project_dialog())

    # ⌘O / Ctrl+O  打开项目
    _bind(window, "Ctrl+O", lambda: window.open_open_project_dialog())

    # ⌘P / Ctrl+P  聚焦到资源面板（打开资源）
    _bind(window, "Ctrl+P", lambda: _focus_assets(window))

    # ── 构建/运行 ─────────────────────────────────

    # ⌘B / Ctrl+B  构建并运行项目
    _bind(window, "Ctrl+B", lambda: window.build_and_run())

    # F5  启动或附加调试器
    _bind(window, "F5", lambda: window.start_debugger())

    # ── 编辑器操作 ────────────────────────────────

    # ⌘Z / Ctrl+Z  撤销
    _bind(window, "Ctrl+Z", lambda: _editor_op(ws, "undo"))

    # ⌘Shift+Z / Ctrl+Y  重做
    _bind(window, "Ctrl+Shift+Z", lambda: _editor_op(ws, "redo"))
    _bind(window, "Ctrl+Y",       lambda: _editor_op(ws, "redo"))

    # ⌘F / Ctrl+F  在当前编辑器中查找
    _bind(window, "Ctrl+F", lambda: _editor_op(ws, "show_find"))

    # Escape  关闭查找栏（在编辑器里由 FindBar 自己处理，这里是全局兜底）
    _bind(window, "Escape", lambda: _editor_op(ws, "hide_find"))

    # ── 搜索 ──────────────────────────────────────

    # ⌘Shift+F / Ctrl+Shift+F  在文件中搜索
    _bind(window, "Ctrl+Shift+F", lambda: window.open_search_in_files())

    # ── 面板切换 ──────────────────────────────────

    # ⌘1  切换资源面板
    _bind(window, "Ctrl+1",
          lambda: window.assets_dock.setVisible(
              not window.assets_dock.isVisible()))

    # ⌘2  切换修改文件面板
    _bind(window, "Ctrl+2",
          lambda: window.changed_files_dock.setVisible(
              not window.changed_files_dock.isVisible()))

    # ⌘3  切换底部面板（控制台）
    _bind(window, "Ctrl+3",
          lambda: window.bottom_dock.setVisible(
              not window.bottom_dock.isVisible()))

    # ⌘`  全屏切换
    _bind(window, "Ctrl+`", lambda: _toggle_fullscreen(window))


# ── 工具函数 ──────────────────────────────────────

def _bind(window, key: str, callback) -> QShortcut:
    """创建快捷键并绑定到 window"""
    sc = QShortcut(QKeySequence(key), window)
    sc.setContext(Qt.ApplicationShortcut)
    sc.activated.connect(callback)
    return sc


def _editor_op(workspace, method: str) -> None:
    """对当前激活的编辑器调用指定方法（如果该编辑器支持）"""
    tab_id = workspace._tab_bar.active_id
    if tab_id and tab_id in workspace._editors:
        editor = workspace._editors[tab_id]
        fn = getattr(editor, method, None)
        if callable(fn):
            fn()


def _focus_assets(window) -> None:
    """显示并聚焦资源面板"""
    dock = window.assets_dock
    if not dock.isVisible():
        dock.setVisible(True)
    dock.raise_()
    dock.setFocus()


def _toggle_fullscreen(window) -> None:
    if window.isFullScreen():
        window.showNormal()
    else:
        window.showFullScreen()