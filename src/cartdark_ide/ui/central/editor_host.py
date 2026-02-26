"""
CartDark IDE · ui/central/editor_host.py
单文件编辑器。当前使用 QPlainTextEdit，带行号区域。
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QTextEdit,
    QSizePolicy, QLineEdit, QPushButton, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QRect, QSize, Signal
from ..theme import theme
from PySide6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QFontMetrics,
    QTextCharFormat, QSyntaxHighlighter, QTextDocument
)


# ──────────────────────────────────────────────
# 行号区域
# ──────────────────────────────────────────────

class _LineNumberArea(QWidget):
    def __init__(self, editor: "_CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


# ──────────────────────────────────────────────
# 简易 Lua 语法高亮
# ──────────────────────────────────────────────

class _LuaHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)

        self._rules: list[tuple] = []

        def fmt(color: str, bold=False, italic=False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            return f

        import re

        keywords = [
            "and", "break", "do", "else", "elseif", "end", "false",
            "for", "function", "goto", "if", "in", "local", "nil",
            "not", "or", "repeat", "return", "then", "true", "until", "while"
        ]
        kw_fmt = fmt("#c678dd", bold=True)
        for kw in keywords:
            self._rules.append((re.compile(rf'\b{kw}\b'), kw_fmt))

        # 字符串
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), fmt("#98c379")))
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), fmt("#98c379")))

        # 数字
        self._rules.append((re.compile(r'\b\d+(\.\d+)?\b'), fmt("#d19a66")))

        # 单行注释
        self._rules.append((re.compile(r'--[^\n]*'), fmt("#5c6370", italic=True)))

        # 内置函数
        builtins = ["print", "pairs", "ipairs", "type", "tostring", "tonumber",
                    "require", "math", "table", "string", "io", "os"]
        bi_fmt = fmt("#61afef")
        for b in builtins:
            self._rules.append((re.compile(rf'\b{b}\b'), bi_fmt))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ──────────────────────────────────────────────
# 代码编辑器（带行号）
# ──────────────────────────────────────────────

class _CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        font = QFont("JetBrains Mono, Menlo, Consolas, monospace")
        font.setPointSize(13)
        font.setFixedPitch(True)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(
            QFontMetrics(self.font()).horizontalAdvance(' ') * 4
        )

        self._line_number_area = _LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._apply_theme_style()
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_width()
        self._highlight_current_line()

    def _apply_theme_style(self):
        t = theme
        if t.is_dark():
            bg, fg, sel = "#1e1e1e", "#abb2bf", "#3e4451"
            ln_bg, ln_fg = "#1e1e1e", "#5c6370"
        else:
            bg, fg, sel = "#ffffff", "#383a42", "#cce5ff"
            ln_bg, ln_fg = "#f5f5f5", "#9d9d9d"
        self._ln_bg = ln_bg
        self._ln_fg = ln_fg
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {bg};
                color: {fg};
                border: none;
                selection-background-color: {sel};
            }}
        """)
        # 刷新行号区
        self._line_number_area.update()
        self._highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance('9') * digits + 8

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(getattr(self, "_ln_bg", "#1a1a1a")))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(getattr(self, "_ln_fg", "#4a4a4a")))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    str(block_number + 1)
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def _update_line_number_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def _highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(theme.BG_PANEL if not theme.is_dark() else "#282c34")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
        self.setExtraSelections(extra)


# ──────────────────────────────────────────────
# EditorHost：单文件编辑器容器
# ──────────────────────────────────────────────

class EditorHost(QWidget):
    """
    单文件编辑器（纯文本 + 语法高亮）。

    信号
    ----
    modified_changed(bool)   文件修改状态变化
    """

    modified_changed = Signal(bool)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._modified = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._editor = _CodeEditor()
        layout.addWidget(self._editor)

        # 查找栏（初始隐藏，底部）
        self._find_bar = _FindBar(self._editor)
        self._find_bar.setVisible(False)
        layout.addWidget(self._find_bar)

        # 加载文件内容
        self._load_file()

        # 根据扩展名附加高亮器
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".lua":
            self._highlighter = _LuaHighlighter(self._editor.document())

        # 监听修改
        self._editor.document().modificationChanged.connect(self._on_modified)
        # 监听主题切换
        theme.changed.connect(self._on_theme_changed)

    # ── 公开 API ──────────────────────────────

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def modified(self) -> bool:
        return self._modified

    def save(self) -> bool:
        """保存文件，返回是否成功"""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
            self._editor.document().setModified(False)
            return True
        except OSError:
            return False

    # ── 内部 ──────────────────────────────────

    def _load_file(self):
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            content = f"# 无法读取文件：{self._file_path}"

        self._editor.setPlainText(content)
        self._editor.document().setModified(False)

    def show_find(self):
        """显示/聚焦查找栏 (⌘F)"""
        self._find_bar.setVisible(True)
        self._find_bar.focus()

    def hide_find(self):
        """隐藏查找栏"""
        self._find_bar.setVisible(False)
        self._editor.setFocus()

    def undo(self):
        self._editor.undo()

    def redo(self):
        self._editor.redo()

    def _on_theme_changed(self, _name: str):
        self._editor._apply_theme_style()
        self._find_bar.apply_theme()

    def _on_modified(self, modified: bool):
        self._modified = modified
        self.modified_changed.emit(modified)


class _FindBar(QWidget):
    """
    内嵌查找栏，显示在编辑器底部。
    支持：向前/向后查找、大小写匹配、Esc 关闭。
    """

    def __init__(self, editor: "_CodeEditor", parent=None):
        super().__init__(parent)
        self._editor = editor
        self._matches: list = []
        self._cur_idx: int = -1

        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("查找...")
        self._input.setFixedWidth(220)
        self._input.textChanged.connect(self._do_find)
        self._input.returnPressed.connect(self._find_next)
        layout.addWidget(self._input)

        self._case_cb = QCheckBox("区分大小写")
        self._case_cb.stateChanged.connect(self._do_find)
        layout.addWidget(self._case_cb)

        self._info_lbl = QLabel("")
        self._info_lbl.setFixedWidth(80)
        layout.addWidget(self._info_lbl)

        layout.addStretch()

        self._prev_btn = QPushButton("↑")
        self._prev_btn.setFixedSize(28, 24)
        self._prev_btn.setToolTip("上一个 (Shift+Enter)")
        self._prev_btn.clicked.connect(self._find_prev)
        layout.addWidget(self._prev_btn)

        self._next_btn = QPushButton("↓")
        self._next_btn.setFixedSize(28, 24)
        self._next_btn.setToolTip("下一个 (Enter)")
        self._next_btn.clicked.connect(self._find_next)
        layout.addWidget(self._next_btn)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.clicked.connect(self.hide)
        layout.addWidget(self._close_btn)

        self.apply_theme()

    def focus(self):
        self._input.setFocus()
        self._input.selectAll()

    def apply_theme(self):
        t = theme
        self.setStyleSheet(f"background: {t.BG_PANEL}; border-top: 1px solid {t.BORDER};")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {t.BG_WIDGET_ALT};
                color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {t.BORDER_FOCUS}; }}
        """)
        self._case_cb.setStyleSheet(f"""
            QCheckBox {{ color: {t.FG_SECONDARY}; font-size: 12px; }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                background: {t.BG_WIDGET_ALT};
                border: 1px solid {t.BORDER_INPUT};
                border-radius: 2px;
            }}
            QCheckBox::indicator:checked {{
                background: {t.ACCENT}; border-color: {t.ACCENT};
            }}
        """)
        self._info_lbl.setStyleSheet(f"color: {t.FG_MUTED}; font-size: 12px;")
        btn_style = f"""
            QPushButton {{
                background: {t.BTN_BG}; color: {t.FG_PRIMARY};
                border: 1px solid {t.BORDER_INPUT}; border-radius: 3px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {t.BTN_HOVER}; }}
            QPushButton:pressed {{ background: {t.BTN_PRESSED}; }}
        """
        for btn in (self._prev_btn, self._next_btn, self._close_btn):
            btn.setStyleSheet(btn_style)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self._editor.setFocus()
        elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
            self._find_prev()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        # 关闭时清除高亮
        self._clear_highlights()
        super().hideEvent(event)

    def _do_find(self):
        self._clear_highlights()
        text = self._input.text()
        if not text:
            self._info_lbl.setText("")
            self._matches = []
            self._cur_idx = -1
            return

        flags = Qt.CaseSensitive if self._case_cb.isChecked() else Qt.CaseInsensitive
        doc = self._editor.document()
        cursor = doc.find(text, 0, flags)
        self._matches = []
        while not cursor.isNull():
            self._matches.append(cursor)
            cursor = doc.find(text, cursor, flags)

        # 高亮所有匹配
        extra_sels = []
        t = theme
        for c in self._matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = c
            sel.format.setBackground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(
                "#d4c500" if t.is_dark() else "#ffff00"
            ))
            extra_sels.append(sel)
        self._editor.setExtraSelections(extra_sels)

        count = len(self._matches)
        if count > 0:
            self._cur_idx = 0
            self._jump_to(0)
            self._info_lbl.setText(f"1 / {count}")
        else:
            self._cur_idx = -1
            self._info_lbl.setText("无结果")

    def _find_next(self):
        if not self._matches:
            return
        self._cur_idx = (self._cur_idx + 1) % len(self._matches)
        self._jump_to(self._cur_idx)

    def _find_prev(self):
        if not self._matches:
            return
        self._cur_idx = (self._cur_idx - 1) % len(self._matches)
        self._jump_to(self._cur_idx)

    def _jump_to(self, idx: int):
        cursor = self._matches[idx]
        self._editor.setTextCursor(cursor)
        self._editor.ensureCursorVisible()
        self._info_lbl.setText(f"{idx + 1} / {len(self._matches)}")

    def _clear_highlights(self):
        self._editor.setExtraSelections([])



def make_editor(file_path: str, parent=None) -> QWidget:
    """
    工厂函数：根据文件扩展名返回合适的编辑器。
    返回的对象保证有 file_path / modified 属性和 save() / modified_changed 信号。
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".input_binding":
        from .input_binding_editor import InputBindingEditor
        return InputBindingEditor(file_path, parent)
    if ext == ".cart":
        from .cart_editor import CartEditor
        return CartEditor(file_path, parent)
    return EditorHost(file_path, parent)