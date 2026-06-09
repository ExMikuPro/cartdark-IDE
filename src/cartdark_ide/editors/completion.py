from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QToolTip

from ..ui.central import api_catalog
from ..ui.theme import theme


@dataclass(frozen=True)
class CompletionItem:
    label: str
    insert_text: str
    kind: str = "keyword"
    detail: str = ""
    documentation: str = ""


@dataclass(frozen=True)
class CompletionContext:
    language: str
    file_path: str
    text_before_cursor: str
    current_line: str
    prefix: str
    replace_length: int
    manual: bool = False


class CompletionProvider:
    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        return []


def _completion_item(item: api_catalog.ApiItem) -> CompletionItem:
    return CompletionItem(
        label=item.label,
        insert_text=item.insert_text,
        kind=item.kind,
        detail=item.detail,
        documentation=item.documentation,
    )


def _completion_items(items: list[api_catalog.ApiItem]) -> list[CompletionItem]:
    return [_completion_item(item) for item in items]


class CartDarkLuaCompletionProvider(CompletionProvider):
    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        event_prefix = self._string_prefix_after(context, r'action\.event\s*==\s*["\']')
        if event_prefix is not None:
            return self._with_prefix(_completion_items(api_catalog.ACTION_EVENTS), event_prefix)

        action_prefix = self._string_prefix_after(context, r'action_id\s*==\s*["\']')
        if action_prefix is not None:
            actions = [
                CompletionItem(name, name, "constant", "input action", "Action id read from input/*.input_binding.")
                for name in _input_actions_for(context.file_path)
            ]
            return self._with_prefix(actions, action_prefix)

        layer_prefix = self._string_prefix_after(
            context,
            r'layer\.(?:enable|disable|set_enabled|is_enabled|set_alpha|get_alpha)\(\s*["\']',
        )
        if layer_prefix is not None:
            layers = [
                CompletionItem(name, name, "constant", "layer name", "Layer name available to layer.* APIs.")
                for name in _layer_names_for(context.file_path)
            ]
            return self._with_prefix(layers, layer_prefix)

        member = re.search(r'\b([A-Za-z_][A-Za-z0-9_]*)[.:]([A-Za-z_][A-Za-z0-9_]*)?$', context.text_before_cursor)
        if member:
            owner, prefix = member.groups()
            return self._with_prefix(_completion_items(api_catalog.MODULE_APIS.get(owner, [])), prefix or "")

        ui_config = re.search(r'\bui\.(button|slider|image)\s*\([^)]*\{[^}]*["\']?([A-Za-z_]*)$', context.current_line)
        if ui_config:
            widget, prefix = ui_config.groups()
            return self._with_prefix(_completion_items(api_catalog.UI_CONFIG_FIELDS[widget]), prefix)

        if context.manual or len(context.prefix) >= 2:
            candidates = _completion_items([
                *api_catalog.LIFECYCLE_SNIPPETS,
                *api_catalog.GLOBAL_APIS,
                *api_catalog.LUA_WORD_COMPLETIONS,
            ])
            return self._with_prefix(candidates, context.prefix)
        return []

    def _string_prefix_after(self, context: CompletionContext, pattern: str) -> Optional[str]:
        match = re.search(pattern + r'([A-Za-z0-9_./-]*)$', context.text_before_cursor)
        if match:
            return match.group(1)
        return None

    def _with_prefix(self, items: list[CompletionItem], prefix: str) -> list[CompletionItem]:
        if not prefix:
            return items
        low = prefix.lower()
        return [item for item in items if item.label.lower().startswith(low)]


class JsonCompletionProvider(CompletionProvider):
    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        event_value_prefix = self._json_string_value_prefix(context, "event")
        if event_value_prefix is not None:
            return self._with_prefix(_completion_items(api_catalog.ACTION_EVENTS), event_value_prefix)

        action_value_prefix = self._json_string_value_prefix(context, "action")
        if action_value_prefix is not None:
            actions = [
                CompletionItem(name, name, "constant", "input action", "Action id read from input/*.input_binding.")
                for name in _input_actions_for(context.file_path)
            ]
            return self._with_prefix(actions, action_value_prefix)

        key_prefix = self._json_key_prefix(context)
        if key_prefix is None and not context.manual:
            return []

        ext = os.path.splitext(context.file_path)[1].lower()
        if ext == ".cart":
            keys = api_catalog.CART_KEYS
        elif ext == ".layer":
            keys = api_catalog.LAYER_KEYS
        elif ext == ".input_binding":
            keys = api_catalog.INPUT_BINDING_KEYS
        else:
            keys = [*api_catalog.CART_KEYS, *api_catalog.LAYER_KEYS, *api_catalog.INPUT_BINDING_KEYS]
        return self._with_prefix(_completion_items(keys), key_prefix or context.prefix)

    def _json_key_prefix(self, context: CompletionContext) -> Optional[str]:
        match = re.search(r'(?:^\s*|[,{]\s*)"?([A-Za-z_][A-Za-z0-9_]*)?$', context.current_line)
        if match:
            return match.group(1) or ""
        return None

    def _json_string_value_prefix(self, context: CompletionContext, key: str) -> Optional[str]:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"([A-Za-z0-9_./-]*)$', context.text_before_cursor)
        if match:
            return match.group(1)
        return None

    def _with_prefix(self, items: list[CompletionItem], prefix: str) -> list[CompletionItem]:
        if not prefix:
            return items
        low = prefix.lower()
        return [item for item in items if item.label.lower().startswith(low)]


class EditorCompleter:
    def __init__(self, editor: QPlainTextEdit, language: str, file_path: str):
        self._editor = editor
        self._language = language
        self._file_path = file_path
        self._items_by_label: dict[str, CompletionItem] = {}
        self._replace_length = 0

        self._model = QStringListModel()
        self._completer = QCompleter(self._model, editor)
        self._completer.setWidget(editor)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchStartsWith)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.activated[str].connect(self._insert_completion)
        self._completer.highlighted[str].connect(self._show_completion_detail)
        self.apply_theme()

    def apply_theme(self) -> None:
        popup = self._completer.popup()
        popup.setStyleSheet(f"""
            QListView {{
                background: {theme.BG_PANEL};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BORDER_INPUT};
                selection-background-color: {theme.BG_SELECTED};
                selection-color: {theme.FG_TITLE};
                padding: 2px;
            }}
        """)

    def is_completion_shortcut(self, event) -> bool:
        mods = event.modifiers()
        if event.key() == Qt.Key_Space and mods & Qt.ControlModifier:
            return True
        if event.key() == Qt.Key_Slash and mods & Qt.AltModifier:
            return True
        return False

    def is_popup_key(self, event) -> bool:
        return self._completer.popup().isVisible() and event.key() in {
            Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab,
        }

    def maybe_show_after_key(self, event) -> None:
        text = event.text()
        if text in {".", ":", '"', "'"}:
            self.show(manual=False)
            return
        if self._completer.popup().isVisible() and (text or event.key() == Qt.Key_Backspace):
            self.show(manual=False)
            return
        if text and (text.isalnum() or text == "_"):
            context = self._context(manual=False)
            if len(context.prefix) >= 2:
                self.show(manual=False)

    def show(self, manual: bool) -> None:
        context = self._context(manual=manual)
        provider = self._provider()
        if provider is None:
            self.hide()
            return

        items = provider.complete(context)
        if not items:
            self.hide()
            return

        self._items_by_label = {}
        labels = []
        for item in items:
            if item.label in self._items_by_label:
                continue
            self._items_by_label[item.label] = item
            labels.append(item.label)
        self._replace_length = context.replace_length
        self._model.setStringList(labels)
        self._completer.setCompletionPrefix(context.prefix)
        if self._completer.completionCount() == 0:
            self.hide()
            return

        rect = self._editor.cursorRect()
        rect.setWidth(max(260, self._completer.popup().sizeHintForColumn(0) + 24))
        self._completer.complete(rect)

    def hide(self) -> None:
        self._completer.popup().hide()
        QToolTip.hideText()

    def _provider(self) -> Optional[CompletionProvider]:
        if self._language == "lua":
            return CartDarkLuaCompletionProvider()
        if self._language == "json":
            return JsonCompletionProvider()
        return None

    def _context(self, manual: bool) -> CompletionContext:
        cursor = self._editor.textCursor()
        before_cursor = self._editor.toPlainText()[:cursor.position()]
        block_text = cursor.block().text()
        current_line = block_text[:cursor.positionInBlock()]

        prefix = ""
        replace_length = 0
        string_match = re.search(r'["\']([A-Za-z0-9_./-]*)$', current_line)
        member_match = re.search(r'\b[A-Za-z_][A-Za-z0-9_]*[.:]([A-Za-z_][A-Za-z0-9_]*)?$', current_line)
        word_match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)$', current_line)
        if string_match:
            prefix = string_match.group(1)
            replace_length = len(prefix)
        elif member_match:
            prefix = member_match.group(1) or ""
            replace_length = len(prefix)
        elif word_match:
            prefix = word_match.group(1)
            replace_length = len(prefix)

        return CompletionContext(
            language=self._language,
            file_path=self._file_path,
            text_before_cursor=before_cursor,
            current_line=current_line,
            prefix=prefix,
            replace_length=replace_length,
            manual=manual,
        )

    def _insert_completion(self, label: str) -> None:
        item = self._items_by_label.get(label)
        if item is None:
            return

        cursor = self._editor.textCursor()
        replace_length = self._replace_length
        if item.kind == "snippet" and item.insert_text.startswith("function "):
            function_prefix = self._function_prefix_before_cursor(cursor)
            if function_prefix:
                replace_length = len(function_prefix)

        if replace_length:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, replace_length)
            cursor.removeSelectedText()

        text = item.insert_text
        marker = "{cursor}"
        marker_index = text.find(marker)
        if marker_index >= 0:
            text = text.replace(marker, "")

        cursor.insertText(text)
        if marker_index >= 0:
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(text) - marker_index)
        self._editor.setTextCursor(cursor)

    def _function_prefix_before_cursor(self, cursor) -> str:
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        match = re.search(r'((?:local\s+)?function\s+[A-Za-z_][A-Za-z0-9_]*)$', current_line)
        if match:
            return match.group(1)
        return ""

    def _show_completion_detail(self, label: str) -> None:
        item = self._items_by_label.get(label)
        if item is None or (not item.detail and not item.documentation):
            QToolTip.hideText()
            return

        lines = [f"<b>{item.label}</b>"]
        if item.detail:
            lines.append(item.detail)
        if item.documentation:
            lines.append(item.documentation)
        popup = self._completer.popup()
        QToolTip.showText(popup.mapToGlobal(popup.rect().topRight()), "<br>".join(lines), popup)


def _project_root_for(file_path: str) -> str:
    start = os.path.dirname(os.path.abspath(file_path))
    current = start
    while current and current != os.path.dirname(current):
        try:
            if any(name.endswith(".cart") for name in os.listdir(current)):
                return current
        except OSError:
            pass
        current = os.path.dirname(current)
    return start


def _input_actions_for(file_path: str) -> list[str]:
    root = _project_root_for(file_path)
    candidates: list[str] = []
    if file_path.endswith(".input_binding"):
        candidates.append(file_path)
    input_dir = os.path.join(root, "input")
    if os.path.isdir(input_dir):
        for name in sorted(os.listdir(input_dir)):
            if name.endswith(".input_binding"):
                candidates.append(os.path.join(input_dir, name))

    actions: set[str] = set()
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("pin_triggers", "touch_triggers", "gamepad_triggers"):
            for trigger in data.get(key, []):
                action = trigger.get("action") if isinstance(trigger, dict) else None
                if isinstance(action, str) and action:
                    actions.add(action)
    return sorted(actions)


def _layer_names_for(file_path: str) -> list[str]:
    names = {"background", "overlay"}
    root = _project_root_for(file_path)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in {".git", ".venv", "__pycache__"}]
        for filename in filenames:
            if not filename.endswith(".layer"):
                continue
            path = os.path.join(dirpath, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            for key in ("name", "id"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    names.add(value)
    return sorted(names)
