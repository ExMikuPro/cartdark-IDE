"""
CartDark IDE · ui/central/editor_host.py
单文件编辑器。当前使用 QPlainTextEdit，带行号区域。
"""
from __future__ import annotations

import os
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QTextEdit,
    QLineEdit, QPushButton, QLabel, QCheckBox, QToolTip
)
from PySide6.QtCore import Qt, QRect, QSize, Signal
from ..ui.central import api_catalog
from ..ui.theme import theme
from PySide6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QFontMetrics,
    QTextCharFormat, QSyntaxHighlighter, QTextDocument, QTextCursor
)

from .completion import EditorCompleter


def _format(color: str, bold=False, italic=False, background: Optional[str] = None) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if background is not None:
        f.setBackground(QColor(background))
    if bold:
        f.setFontWeight(700)
    if italic:
        f.setFontItalic(True)
    return f


def _language_for_path(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".lua":
        return "lua"
    if ext in {".cart", ".input_binding", ".json", ".layer"}:
        return "json"
    if ext == ".md":
        return "markdown"
    return "plaintext"


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
        self._capture_rules: list[tuple] = []
        self._literal_rules: list[tuple] = []
        self._build_rules()

    def _build_rules(self):
        self._rules.clear()
        self._capture_rules.clear()
        self._literal_rules.clear()
        colors = theme.LUA_DARCULA_COLORS

        constants = {"nil", "true", "false"}
        kw_fmt = _format(colors["keyword"], bold=True)
        const_fmt = _format(colors["constant"], bold=True)
        for kw in api_catalog.LUA_KEYWORDS:
            if kw in constants:
                self._rules.append((re.compile(rf'\b{kw}\b'), const_fmt))
                continue
            self._rules.append((re.compile(rf'\b{kw}\b'), kw_fmt))

        # 数字
        self._rules.append((re.compile(r'\b0[xX][0-9A-Fa-f]+\b'), _format(colors["number"])))
        self._rules.append((re.compile(r'\b\d+(\.\d+)?\b'), _format(colors["number"])))

        # 内置函数
        bi_fmt = _format(colors["api_module"])
        for b in api_catalog.LUA_BUILTINS:
            self._rules.append((re.compile(rf'\b{b}\b'), bi_fmt))
        special_fmt = _format(colors["self"], bold=True)
        for name in api_catalog.LUA_SPECIAL_NAMES:
            self._rules.append((re.compile(rf'\b{name}\b'), special_fmt))

        # CartDark Lua script API names.
        module_fmt = _format(colors["api_module"], bold=True)
        function_fmt = _format(colors["api_function"], bold=True)
        lifecycle_fmt = _format(colors["lifecycle"], bold=True)
        for name in api_catalog.module_names():
            self._rules.append((re.compile(rf'\b{name}\b'), module_fmt))
        for module, entries in api_catalog.MODULE_APIS.items():
            if module in {"self", "action"}:
                continue
            function_names = [entry.label.split("(", 1)[0] for entry in entries]
            if not function_names:
                continue
            function_pattern = "|".join(re.escape(name) for name in function_names)
            self._capture_rules.append((
                re.compile(rf'\b{re.escape(module)}\s*[.:]\s*({function_pattern})\b'),
                function_fmt,
                1,
            ))
        lifecycle_pattern = "|".join(re.escape(name) for name in api_catalog.lifecycle_names())
        self._capture_rules.append((
            re.compile(rf'\b(?:local\s+)?function\s+({lifecycle_pattern})\s*\('),
            lifecycle_fmt,
            1,
        ))
        self._capture_rules.append((
            re.compile(r'\b(?:local\s+)?function\s+((?!(?:start|input)\s*\()[A-Za-z_][A-Za-z0-9_.:]*)\s*\('),
            function_fmt,
            1,
        ))
        self._rules.append((re.compile(r'[+\-*/%^#=~<>]'), _format(colors["operator"])))
        self._rules.append((re.compile(r'[()\[\]{},.;:]'), _format(colors["punctuation"])))

        # 字符串与注释放在后面，避免关键字覆盖字符串/注释
        self._literal_rules.append((re.compile(r'\[\[[\s\S]*?\]\]'), _format(colors["string"])))
        self._literal_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), _format(colors["string"])))
        self._literal_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), _format(colors["string"])))
        self._literal_rules.append((re.compile(r'--\[\[[\s\S]*?\]\]'), _format(colors["comment"], italic=True)))
        self._literal_rules.append((re.compile(r'--[^\n]*'), _format(colors["comment"], italic=True)))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
        for pattern, fmt, group in self._capture_rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(group), m.end(group) - m.start(group), fmt)
        for pattern, fmt in self._literal_rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class _JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._rules: list[tuple] = [
            (re.compile(r'"(?:[^"\\]|\\.)*"'), _format("#98c379")),
            (re.compile(r'\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b'), _format("#d19a66")),
            (re.compile(r'\b(?:true|false|null)\b'), _format("#c678dd", bold=True)),
            (re.compile(r'[{}\[\]]'), _format("#abb2bf", bold=True)),
            (re.compile(r'"(?:[^"\\]|\\.)*"(?=\s*:)'), _format("#61afef", bold=True)),
        ]

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
        self.setMouseTracking(True)
        self.setTabStopDistance(
            QFontMetrics(self.font()).horizontalAdvance(' ') * 4
        )

        self._line_number_area = _LineNumberArea(self)
        self._current_line_selection = None
        self._search_extra_selections: list = []
        self._bracket_extra_selections: list = []
        self._completion: Optional[EditorCompleter] = None
        self._language = "plaintext"

        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._apply_theme_style()
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_width()
        self._highlight_current_line()

    def configure_completion(self, language: str, file_path: str) -> None:
        self._language = language
        if language in {"lua", "json"}:
            self._completion = EditorCompleter(self, language, file_path)
        else:
            self._completion = None

    def refresh_completion_theme(self) -> None:
        if self._completion is not None:
            self._completion.apply_theme()

    def keyPressEvent(self, event):
        if self._completion is not None:
            if self._completion.is_completion_shortcut(event):
                self._completion.show(manual=True)
                return
            if self._completion.is_popup_key(event):
                event.ignore()
                return

        if self._language == "lua":
            if self._handle_lua_tab(event):
                return
            if self._handle_lua_enter(event):
                return
            if self._handle_lua_pair_input(event):
                return

        super().keyPressEvent(event)

        if self._language == "lua":
            self._maybe_dedent_lua_closer()
            self._update_bracket_matches()

        if self._completion is not None:
            self._completion.maybe_show_after_key(event)

    def _handle_lua_enter(self, event) -> bool:
        if event.key() not in {Qt.Key_Return, Qt.Key_Enter}:
            return False
        cursor = self.textCursor()
        before_cursor = cursor.block().text()[:cursor.positionInBlock()]
        indent = re.match(r'\s*', before_cursor).group(0)
        stripped = before_cursor.strip()
        if self._lua_line_opens_block(stripped):
            indent += " " * 4
        cursor.insertText("\n" + indent)
        self.setTextCursor(cursor)
        self._update_bracket_matches()
        return True

    def _lua_line_opens_block(self, stripped: str) -> bool:
        if not stripped:
            return False
        return bool(
            re.search(r'\bthen\s*$', stripped)
            or re.search(r'\bdo\s*$', stripped)
            or re.search(r'\brepeat\s*$', stripped)
            or re.search(r'\{\s*$', stripped)
            or re.match(r'(?:local\s+)?function\b', stripped)
        )

    def _handle_lua_tab(self, event) -> bool:
        if event.key() == Qt.Key_Tab and not (event.modifiers() & Qt.ShiftModifier):
            self._indent_selection_or_cursor()
            return True
        if event.key() == Qt.Key_Backtab or (
            event.key() == Qt.Key_Tab and event.modifiers() & Qt.ShiftModifier
        ):
            self._outdent_selection_or_cursor()
            return True
        return False

    def _indent_selection_or_cursor(self) -> None:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.insertText(" " * 4)
            self.setTextCursor(cursor)
            return
        self._replace_selected_lines(lambda line: " " * 4 + line)

    def _outdent_selection_or_cursor(self) -> None:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            block_text = cursor.block().text()
            pos_in_block = cursor.positionInBlock()
            remove = min(4, len(block_text) - len(block_text.lstrip(" ")), pos_in_block)
            if remove > 0:
                cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, remove)
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
            return
        self._replace_selected_lines(lambda line: line[4:] if line.startswith(" " * 4) else line.lstrip(" "))

    def _replace_selected_lines(self, transform) -> None:
        cursor = self.textCursor()
        text = self.toPlainText()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        selected = text[line_start:line_end]
        replacement = "\n".join(transform(line) for line in selected.split("\n"))
        cursor.setPosition(line_start)
        cursor.setPosition(line_end, QTextCursor.KeepAnchor)
        cursor.insertText(replacement)
        self.setTextCursor(cursor)

    def _handle_lua_pair_input(self, event) -> bool:
        pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
        text = event.text()
        if text not in pairs:
            return False
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        cursor.insertText(text + pairs[text])
        cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)
        self._update_bracket_matches()
        if self._completion is not None and text in {'"', "'"}:
            self._completion.show(manual=False)
        return True

    def _maybe_dedent_lua_closer(self) -> None:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        stripped = block_text.strip()
        if stripped not in {"end", "else", "until"} and not stripped.startswith("elseif"):
            return
        leading = len(block_text) - len(block_text.lstrip(" "))
        if leading < 4:
            return
        position = cursor.position()
        remove_cursor = QTextCursor(cursor.block())
        remove_cursor.setPosition(cursor.block().position())
        remove_cursor.setPosition(cursor.block().position() + 4, QTextCursor.KeepAnchor)
        remove_cursor.removeSelectedText()
        cursor.setPosition(max(cursor.block().position(), position - 4))
        self.setTextCursor(cursor)

    def mouseMoveEvent(self, event):
        hover = self._api_hover_text_at(event.position().toPoint())
        if hover:
            QToolTip.showText(self.mapToGlobal(event.position().toPoint()), hover, self)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)

    def _api_hover_text_at(self, pos) -> str:
        cursor = self.cursorForPosition(pos)
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', word or ""):
            return ""

        text = self.toPlainText()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        candidates = []

        if start > 1 and text[start - 1] == ".":
            prev_end = start - 1
            prev_start = prev_end
            while prev_start > 0 and re.match(r'[A-Za-z0-9_]', text[prev_start - 1]):
                prev_start -= 1
            previous = text[prev_start:prev_end]
            if previous:
                candidates.append(f"{previous}.{word}")

        if end < len(text) and text[end:end + 1] == ".":
            next_start = end + 1
            next_end = next_start
            while next_end < len(text) and re.match(r'[A-Za-z0-9_]', text[next_end]):
                next_end += 1
            following = text[next_start:next_end]
            if following:
                candidates.append(f"{word}.{following}")

        candidates.append(word)
        for symbol in candidates:
            hover = api_catalog.hover_text(symbol)
            if hover:
                return hover
        return ""

    def _apply_theme_style(self):
        colors = theme.LUA_DARCULA_COLORS
        bg, fg, sel = colors["background"], colors["foreground"], colors["selection"]
        ln_bg, ln_fg = colors["background"], colors["line_number"]
        self._ln_bg = ln_bg
        self._ln_fg = ln_fg
        self._ln_current_fg = colors["current_line_number"]
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

    def set_search_extra_selections(self, selections: list):
        self._search_extra_selections = selections
        self._refresh_extra_selections()

    def clear_search_extra_selections(self):
        self._search_extra_selections = []
        self._refresh_extra_selections()

    def _refresh_extra_selections(self):
        extra = []
        if self._current_line_selection is not None:
            extra.append(self._current_line_selection)
        extra.extend(self._bracket_extra_selections)
        extra.extend(self._search_extra_selections)
        self.setExtraSelections(extra)

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
                if block_number == self.textCursor().blockNumber():
                    painter.setPen(QColor(getattr(self, "_ln_current_fg", "#A9B7C6")))
                else:
                    painter.setPen(QColor(getattr(self, "_ln_fg", "#606366")))
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
        selection = None
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(theme.LUA_DARCULA_COLORS["current_line"])
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
        self._current_line_selection = selection
        self._bracket_extra_selections = self._find_bracket_matches()
        self._refresh_extra_selections()
        self._line_number_area.update()

    def _update_bracket_matches(self) -> None:
        self._bracket_extra_selections = self._find_bracket_matches()
        self._refresh_extra_selections()

    def _find_bracket_matches(self) -> list:
        text = self.toPlainText()
        pos = self.textCursor().position()
        if not text:
            return []

        bracket_pos = -1
        bracket = ""
        if pos > 0 and text[pos - 1] in "()[]{}":
            bracket_pos = pos - 1
            bracket = text[bracket_pos]
        elif pos < len(text) and text[pos] in "()[]{}":
            bracket_pos = pos
            bracket = text[bracket_pos]
        if bracket_pos < 0:
            return []

        pairs = {"(": ")", "[": "]", "{": "}"}
        reverse_pairs = {v: k for k, v in pairs.items()}
        if bracket in pairs:
            match_pos = self._scan_matching_bracket(text, bracket_pos, bracket, pairs[bracket], 1)
        else:
            match_pos = self._scan_matching_bracket(text, bracket_pos, reverse_pairs[bracket], bracket, -1)
        if match_pos < 0:
            return []
        return [self._bracket_selection(bracket_pos), self._bracket_selection(match_pos)]

    def _scan_matching_bracket(self, text: str, start: int, opener: str, closer: str, direction: int) -> int:
        depth = 0
        i = start
        while 0 <= i < len(text):
            ch = text[i]
            if ch == opener:
                depth += direction
            elif ch == closer:
                depth -= direction
            if depth == 0:
                return i
            i += direction
        return -1

    def _bracket_selection(self, pos: int):
        sel = QTextEdit.ExtraSelection()
        sel.cursor = self.textCursor()
        sel.cursor.setPosition(pos)
        sel.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        sel.format.setBackground(QColor(theme.LUA_DARCULA_COLORS["matching_bracket"]))
        sel.format.setForeground(QColor(theme.LUA_DARCULA_COLORS["foreground"]))
        return sel


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
        self._language = _language_for_path(file_path)
        self._highlighter = None
        if self._language == "lua":
            self._highlighter = _LuaHighlighter(self._editor.document())
        elif self._language == "json":
            self._highlighter = _JsonHighlighter(self._editor.document())
        self._editor.configure_completion(self._language, file_path)

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
        self._find_bar.refresh_results()
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
        self._editor.refresh_completion_theme()
        self._find_bar.apply_theme()
        self._find_bar.refresh_results()
        if self._highlighter is not None:
            self._highlighter.rehighlight()

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

        flags = QTextDocument.FindFlags()
        if self._case_cb.isChecked():
            flags = QTextDocument.FindFlag.FindCaseSensitively
        doc = self._editor.document()
        cursor = doc.find(text, 0, flags)
        self._matches = []
        while not cursor.isNull():
            self._matches.append(cursor)
            cursor = doc.find(text, cursor, flags)

        self._apply_match_highlights()

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

    def refresh_results(self):
        if self.isVisible() and self._input.text():
            self._do_find()

    def _apply_match_highlights(self):
        extra_sels = []
        color = QColor(theme.LUA_DARCULA_COLORS["search_match"])
        for c in self._matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = c
            sel.format.setBackground(color)
            extra_sels.append(sel)
        self._editor.set_search_extra_selections(extra_sels)

    def _clear_highlights(self):
        self._editor.clear_search_extra_selections()



def make_editor(file_path: str, parent=None, *, project_root: str = "") -> QWidget:
    """
    工厂函数：根据文件扩展名返回合适的编辑器。
    返回的对象保证有 file_path / modified 属性和 save() / modified_changed 信号。
    """
    ext = os.path.splitext(file_path)[1].lower()
    from .image_viewer import is_supported_image_path
    if is_supported_image_path(file_path):
        from .image_viewer import ImageViewerEditor
        return ImageViewerEditor(file_path, parent, project_root=project_root)
    if ext == ".input_binding":
        from .input_binding_editor import InputBindingEditor
        return InputBindingEditor(file_path, parent)
    if ext == ".cart":
        from .cart_editor import CartEditor
        return CartEditor(file_path, parent)
    if ext == ".layer":
        from .editor2d import Editor2D
        return Editor2D(file_path, parent)
    return EditorHost(file_path, parent)
