"""
CartDark IDE · ui/central/editor_host.py
单文件编辑器。当前使用 QPlainTextEdit，带行号区域。
"""
from __future__ import annotations

import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit, QTextEdit
from PySide6.QtCore import Qt, QRect, QSize, Signal
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

        self.setStyleSheet("""
            QPlainTextEdit {
                background: #1e1e1e;
                color: #abb2bf;
                border: none;
                selection-background-color: #3e4451;
            }
        """)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(
            QFontMetrics(self.font()).horizontalAdvance(' ') * 4
        )

        self._line_number_area = _LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_width()
        self._highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance('9') * digits + 8

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1a1a1a"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#4a4a4a"))
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
            line_color = QColor("#282c34")
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = _CodeEditor()
        layout.addWidget(self._editor)

        # 加载文件内容
        self._load_file()

        # 根据扩展名附加高亮器
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".lua":
            self._highlighter = _LuaHighlighter(self._editor.document())

        # 监听修改
        self._editor.document().modificationChanged.connect(self._on_modified)

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

    def _on_modified(self, modified: bool):
        self._modified = modified
        self.modified_changed.emit(modified)


def make_editor(file_path: str, parent=None) -> QWidget:
    """
    工厂函数：根据文件扩展名返回合适的编辑器。
    返回的对象保证有 file_path / modified 属性和 save() / modified_changed 信号。
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".input_binding":
        from .input_binding_editor import InputBindingEditor
        return InputBindingEditor(file_path, parent)
    return EditorHost(file_path, parent)