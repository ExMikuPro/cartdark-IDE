"""
CartDark IDE · ui/docks/assets_dock.py
资源面板停靠窗口，含完整右键菜单。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from PySide6.QtWidgets import (
    QDockWidget, QTreeView, QMenu, QInputDialog, QMessageBox,
    QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QModelIndex, QPoint

from ..models.assets_fs_model import AssetsFsModel, AssetsItem
from ..delegates.assets_delegate import AssetsDelegate


class AssetsDock(QDockWidget):
    file_activated  = Signal(str, str)  # (abs_path, mode)  mode: "editor" | "text"
    file_deleted    = Signal(str)        # 文件被删除，发出绝对路径
    project_changed = Signal()

    def __init__(self, parent=None):
        super().__init__("资源", parent)
        self.setMinimumWidth(230)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self._model = AssetsFsModel(self)
        self._project_root: str = ""

        self._tree = QTreeView()
        self._tree.setHeaderHidden(True)
        self._tree.setModel(self._model)
        self._tree.setItemDelegate(AssetsDelegate(self._tree))
        self._tree.activated.connect(self._on_item_activated)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self.setWidget(self._tree)

    # ── 公开 API ──────────────────────────────

    def load_project(self, project_root: str, project_name: str = ""):
        self._project_root = os.path.abspath(project_root)
        self._model.load_from_root(project_root, project_name)
        self._tree.expandToDepth(1)

    def close_project(self):
        self._project_root = ""
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["名称"])
        self._model._show_placeholder()

    def on_theme_changed(self):
        from ..icons import clear_cache
        clear_cache()
        self._model.reload_icons()

    # ── 文件激活 ──────────────────────────────

    def _on_item_activated(self, index: QModelIndex):
        item = self._model.itemFromIndex(index)
        if not item:
            return
        abs_path = getattr(item, "_abs_path", "")
        if abs_path and os.path.isfile(abs_path):
            self.file_activated.emit(abs_path, "editor")

    # ── 右键菜单 ──────────────────────────────

    def _on_context_menu(self, pos: QPoint):
        index = self._tree.indexAt(pos)
        global_pos = self._tree.viewport().mapToGlobal(pos)
        if not index.isValid():
            self._show_blank_menu(global_pos)
            return
        item = self._model.itemFromIndex(index)
        if not isinstance(item, AssetsItem) or not item._abs_path:
            return
        abs_path = item._abs_path
        if os.path.isdir(abs_path):
            self._show_dir_menu(abs_path, global_pos)
        else:
            self._show_file_menu(abs_path, global_pos)

    def _show_blank_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("新建文件…",      lambda: self._cmd_new_file(self._project_root))
        menu.addAction("新建 Lua 脚本…", lambda: self._cmd_new_lua(self._project_root))
        menu.addAction("新建文件夹…",    lambda: self._cmd_new_folder(self._project_root))
        menu.addSeparator()
        menu.addAction("导入文件…",   lambda: self._cmd_import(self._project_root))
        menu.addSeparator()
        menu.addAction("刷新",        self._cmd_refresh)
        menu.exec(pos)

    def _show_dir_menu(self, abs_path: str, pos):
        menu = QMenu(self)
        is_root = (abs_path == self._project_root)
        is_res  = (abs_path == os.path.join(self._project_root, "res"))

        if is_root:
            menu.addAction("新建文件…",       lambda: self._cmd_new_file(abs_path))
            menu.addAction("新建 Lua 脚本…",  lambda: self._cmd_new_lua(abs_path))
            menu.addAction("新建文件夹…",     lambda: self._cmd_new_folder(abs_path))
            menu.addSeparator()
            menu.addAction("在访达中显示", lambda: self._cmd_reveal(abs_path))
            menu.addAction("复制路径",     lambda: self._cmd_copy_path(abs_path))
            menu.addSeparator()
            menu.addAction("重新加载项目", self._cmd_refresh)
            menu.addAction("关闭项目",     self._cmd_close_project)
        elif is_res:
            menu.addAction("新建 Lua 脚本…",      lambda: self._cmd_new_lua(abs_path))
            menu.addAction("新建文件夹…",         lambda: self._cmd_new_folder(abs_path))
            menu.addSeparator()
            menu.addAction("导入资源到 res…",     lambda: self._cmd_import(abs_path))
            menu.addAction("导入并写入打包清单…", lambda: self._cmd_import_to_pack(abs_path))
            menu.addSeparator()
            menu.addAction("重命名…",              lambda: self._cmd_rename(abs_path))
            menu.addAction("删除…",                lambda: self._cmd_delete(abs_path))
            menu.addSeparator()
            menu.addAction("在访达中显示",         lambda: self._cmd_reveal(abs_path))
            menu.addAction("复制路径",             lambda: self._cmd_copy_path(abs_path))
        else:
            menu.addAction("新建文件…",       lambda: self._cmd_new_file(abs_path))
            menu.addAction("新建 Lua 脚本…",  lambda: self._cmd_new_lua(abs_path))
            menu.addAction("新建文件夹…",     lambda: self._cmd_new_folder(abs_path))
            menu.addSeparator()
            menu.addAction("导入文件到此处…", lambda: self._cmd_import(abs_path))
            menu.addSeparator()
            menu.addAction("重命名…",         lambda: self._cmd_rename(abs_path))
            menu.addAction("删除…",           lambda: self._cmd_delete(abs_path))
            menu.addSeparator()
            menu.addAction("在访达中显示",    lambda: self._cmd_reveal(abs_path))
            menu.addAction("复制路径",        lambda: self._cmd_copy_path(abs_path))
        menu.exec(pos)

    def _show_file_menu(self, abs_path: str, pos):
        menu = QMenu(self)
        name      = os.path.basename(abs_path)
        is_pack   = (name == "pack.json")
        is_cart   = name.endswith(".cart")
        is_in_res = self._is_under_res(abs_path)

        # 打开于... 子菜单
        open_menu = menu.addMenu("打开于...")
        open_menu.addAction("编辑器", lambda: self.file_activated.emit(abs_path, "editor"))
        open_menu.addAction("文本",   lambda: self.file_activated.emit(abs_path, "text"))
        menu.addSeparator()

        if is_pack:
            menu.addAction("校验打包清单",          lambda: self._cmd_validate_pack())
            menu.addAction("从 res/ 重新生成清单…", lambda: self._cmd_regen_pack())
            menu.addAction("格式化 JSON",           lambda: self._cmd_format_pack())
            menu.addSeparator()
        elif is_cart:
            menu.addAction("校验工程文件", lambda: self._cmd_validate_cart(abs_path))
            menu.addSeparator()
        elif is_in_res:
            menu.addAction("加入打包清单",     lambda: self._cmd_add_to_pack(abs_path))
            menu.addAction("从打包清单移除",   lambda: self._cmd_remove_from_pack(abs_path))
            menu.addAction("在打包清单中定位", lambda: self._cmd_locate_in_pack(abs_path))
            menu.addSeparator()

        menu.addAction("重命名…",      lambda: self._cmd_rename(abs_path))
        menu.addAction("删除…",        lambda: self._cmd_delete(abs_path))
        menu.addAction("复制一份",     lambda: self._cmd_duplicate(abs_path))
        menu.addSeparator()
        menu.addAction("在访达中显示", lambda: self._cmd_reveal(abs_path))
        menu.addAction("复制路径",     lambda: self._cmd_copy_path(abs_path))
        menu.exec(pos)

    # ── 命令 ──────────────────────────────────

    def _cmd_new_lua(self, parent_dir: str):
        """新建 Lua 脚本，并写入 pack.json 的 script chunk"""
        if not parent_dir:
            return
        name, ok = QInputDialog.getText(
            self, "新建 Lua 脚本", "脚本名称（无需输入 .lua）：",
            QLineEdit.Normal, "新脚本"
        )
        if not ok or not name.strip():
            return

        # 自动补 .lua
        raw = name.strip()
        if not raw.endswith(".lua"):
            raw += ".lua"
        # 去掉用户手动加的多余 .lua.lua
        while raw.endswith(".lua.lua"):
            raw = raw[:-4]

        path = os.path.join(parent_dir, raw)
        if os.path.exists(path):
            QMessageBox.warning(self, "新建 Lua 脚本", raw + " 已存在")
            return

        # 生成模板内容
        base = os.path.splitext(raw)[0]
        if base == "main":
            content_text = (
                "function start()\n"
                "  -- 初始化（只调用一次）\n"
                "end\n"
                "\n"
                "function update(dt)\n"
                "  -- dt: 秒（float），默认固定 0.010\n"
                "end\n"
                "\n"
                "function input(action, event)\n"
                "  -- action: 例如 \"ok\" / \"back\" / \"up\"\n"
                "  -- event: \"press\" / \"release\"\n"
                "end\n"
            )
        else:
            content_text = "-- " + raw + "\n"

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content_text)
        except OSError as e:
            QMessageBox.critical(self, "新建 Lua 脚本", str(e))
            return

        # 写入 pack.json
        try:
            from ...project.pack_sync import add_script_to_pack
            add_script_to_pack(self._project_root, path)
        except Exception as e:
            QMessageBox.warning(self, "打包清单", "文件已创建，但写入 pack.json 失败：" + str(e))

        self._cmd_refresh()

    def _cmd_new_file(self, parent_dir: str):
        if not parent_dir:
            return
        name, ok = QInputDialog.getText(self, "新建文件", "文件名：", QLineEdit.Normal, "新文件.txt")
        if not ok or not name.strip():
            return
        path = os.path.join(parent_dir, name.strip())
        if os.path.exists(path):
            QMessageBox.warning(self, "新建文件", name + " 已存在")
            return
        try:
            open(path, "w").close()
            self._cmd_refresh()
        except OSError as e:
            QMessageBox.critical(self, "新建文件", str(e))

    def _cmd_new_folder(self, parent_dir: str):
        if not parent_dir:
            return
        name, ok = QInputDialog.getText(self, "新建文件夹", "文件夹名：", QLineEdit.Normal, "新文件夹")
        if not ok or not name.strip():
            return
        path = os.path.join(parent_dir, name.strip())
        if os.path.exists(path):
            QMessageBox.warning(self, "新建文件夹", name + " 已存在")
            return
        try:
            os.makedirs(path)
            self._cmd_refresh()
        except OSError as e:
            QMessageBox.critical(self, "新建文件夹", str(e))

    def _cmd_rename(self, abs_path: str):
        old_name = os.path.basename(abs_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称：", QLineEdit.Normal, old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_path = os.path.join(os.path.dirname(abs_path), new_name.strip())
        if os.path.exists(new_path):
            QMessageBox.warning(self, "重命名", new_name + " 已存在")
            return
        try:
            os.rename(abs_path, new_path)
            self._pack_sync_rename(abs_path, new_path)
            self._cmd_refresh()
        except OSError as e:
            QMessageBox.critical(self, "重命名", str(e))

    def _cmd_delete(self, abs_path: str):
        name   = os.path.basename(abs_path)
        is_dir = os.path.isdir(abs_path)
        if is_dir:
            non_empty = bool(list(os.scandir(abs_path)))
            msg = (name + " 不是空文件夹，确定要递归删除全部内容吗？"
                   if non_empty else "确定删除文件夹 " + name + "？")
        else:
            msg = "确定删除 " + name + "？此操作不可撤销。"

        btn = QMessageBox.question(self, "删除", msg,
                                   QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if btn != QMessageBox.Yes:
            return
        try:
            shutil.rmtree(abs_path) if is_dir else os.remove(abs_path)
            self._pack_sync_delete(abs_path)
            self.file_deleted.emit(abs_path)
            self._cmd_refresh()
        except OSError as e:
            QMessageBox.critical(self, "删除", str(e))

    def _cmd_duplicate(self, abs_path: str):
        base, ext = os.path.splitext(abs_path)
        new_path = base + "_副本" + ext
        n = 1
        while os.path.exists(new_path):
            new_path = base + "_副本" + str(n) + ext
            n += 1
        try:
            shutil.copy2(abs_path, new_path)
            self._cmd_refresh()
        except OSError as e:
            QMessageBox.critical(self, "复制", str(e))

    def _cmd_import(self, target_dir: str):
        if not target_dir:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "导入文件", os.path.expanduser("~"))
        if not files:
            return
        for src in files:
            dst = os.path.join(target_dir, os.path.basename(src))
            if os.path.exists(dst):
                btn = QMessageBox.question(
                    self, "文件已存在",
                    os.path.basename(src) + " 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.Skip | QMessageBox.Cancel,
                    QMessageBox.Skip)
                if btn == QMessageBox.Cancel:
                    break
                if btn != QMessageBox.Yes:
                    continue
            try:
                shutil.copy2(src, dst)
            except OSError as e:
                QMessageBox.warning(self, "导入", str(e))
        self._cmd_refresh()

    def _cmd_import_to_pack(self, target_dir: str):
        self._cmd_import(target_dir)
        QMessageBox.information(self, "打包清单",
            "文件已导入到 res/。\npack.json 使用 glob 匹配，新文件将自动包含在打包范围内。")

    def _cmd_reveal(self, abs_path: str):
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", abs_path])
        elif sys.platform == "win32":
            subprocess.run(["explorer", "/select,", abs_path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(abs_path)])

    def _cmd_copy_path(self, abs_path: str):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(abs_path)

    def _cmd_refresh(self):
        if not self._project_root:
            return
        expanded = self._get_expanded_paths()
        self._model.load_from_root(self._project_root, os.path.basename(self._project_root))
        self._restore_expanded_paths(expanded)
        self.project_changed.emit()

    def _cmd_close_project(self):
        mw = self.parent()
        if mw and hasattr(mw, "_project_service"):
            mw._project_service.close_project()

    # ── pack.json 命令 ────────────────────────

    def _cmd_validate_pack(self):
        from ...project.pack_sync import validate
        issues = validate(self._project_root)
        if not issues:
            QMessageBox.information(self, "校验打包清单", "未发现问题")
        else:
            QMessageBox.warning(self, "校验打包清单",
                "发现 " + str(len(issues)) + " 个问题：\n\n" +
                "\n".join("• " + i for i in issues))

    def _cmd_regen_pack(self):
        btn = QMessageBox.question(self, "重新生成清单",
            "这将重新生成 pack.json 中的 RES chunk（其他字段保留）。\n确定继续？",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if btn != QMessageBox.Yes:
            return
        from ...project.pack_sync import regenerate_from_res
        if regenerate_from_res(self._project_root):
            QMessageBox.information(self, "重新生成清单", "已完成，请检查 pack.json")
            self._cmd_refresh()
        else:
            QMessageBox.critical(self, "重新生成清单", "操作失败")

    def _cmd_format_pack(self):
        from ...project.pack_sync import format_json
        if format_json(self._project_root):
            QMessageBox.information(self, "格式化", "pack.json 已格式化")
        else:
            QMessageBox.critical(self, "格式化", "操作失败")

    def _cmd_validate_cart(self, cart_path: str):
        issues = []
        pack = os.path.join(self._project_root, "pack.json")
        if not os.path.isfile(pack):
            issues.append("pack.json 不存在")
        for d in ("res", "main", "script", "input"):
            if not os.path.isdir(os.path.join(self._project_root, d)):
                issues.append("目录缺失：" + d + "/")
        if not issues:
            QMessageBox.information(self, "校验工程", "工程结构完整")
        else:
            QMessageBox.warning(self, "校验工程",
                "发现问题：\n\n" + "\n".join("• " + i for i in issues))

    def _cmd_add_to_pack(self, abs_path: str):
        rel = os.path.relpath(abs_path, self._project_root).replace(os.sep, "/")
        QMessageBox.information(self, "加入打包清单",
            "pack.json 使用 glob 匹配 res/**/*，\n" + rel + " 已自动包含在打包范围内。")

    def _cmd_remove_from_pack(self, abs_path: str):
        from ...project.pack_sync import _find_pack_json, _load, _save
        pack_path = _find_pack_json(self._project_root)
        if not pack_path:
            return
        data = _load(pack_path)
        changed = False
        for chunk in data.get("chunks", []):
            if chunk.get("type") == "RES":
                excl = chunk.setdefault("exclude", [])
                pattern = "**/" + os.path.basename(abs_path)
                if pattern not in excl:
                    excl.append(pattern)
                    changed = True
        if changed:
            _save(pack_path, data)
            QMessageBox.information(self, "打包清单",
                os.path.basename(abs_path) + " 已加入排除列表")
        else:
            QMessageBox.information(self, "打包清单", "未找到对应的 RES chunk")

    def _cmd_locate_in_pack(self, abs_path: str):
        pack_path = os.path.join(self._project_root, "pack.json")
        if os.path.isfile(pack_path):
            self.file_activated.emit(pack_path)

    # ── 辅助 ──────────────────────────────────

    def _is_under_res(self, abs_path: str) -> bool:
        if not self._project_root:
            return False
        res = os.path.abspath(os.path.join(self._project_root, "res")) + os.sep
        return os.path.abspath(abs_path).startswith(res)

    def _pack_sync_rename(self, old_abs: str, new_abs: str):
        try:
            from ...project.pack_sync import on_file_renamed
            on_file_renamed(self._project_root, old_abs, new_abs)
        except Exception:
            pass

    def _pack_sync_delete(self, abs_path: str):
        try:
            from ...project.pack_sync import on_file_deleted
            on_file_deleted(self._project_root, abs_path)
        except Exception:
            pass

    def _get_expanded_paths(self) -> set:
        expanded = set()
        def walk(parent_index):
            for row in range(self._model.rowCount(parent_index)):
                idx = self._model.index(row, 0, parent_index)
                if self._tree.isExpanded(idx):
                    item = self._model.itemFromIndex(idx)
                    if isinstance(item, AssetsItem):
                        expanded.add(item._abs_path)
                walk(idx)
        walk(self._tree.rootIndex())
        return expanded

    def _restore_expanded_paths(self, expanded: set):
        def walk(parent_index):
            for row in range(self._model.rowCount(parent_index)):
                idx = self._model.index(row, 0, parent_index)
                item = self._model.itemFromIndex(idx)
                if isinstance(item, AssetsItem) and item._abs_path in expanded:
                    self._tree.setExpanded(idx, True)
                walk(idx)
        walk(self._tree.rootIndex())