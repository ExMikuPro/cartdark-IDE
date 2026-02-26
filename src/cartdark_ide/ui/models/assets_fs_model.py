"""
CartDark IDE · ui/models/assets_fs_model.py
资源面板的数据模型，直接反映项目磁盘目录结构。
"""
from __future__ import annotations

import os
from PySide6.QtGui import QStandardItemModel, QStandardItem
from ..icons import get_icon


# 文件扩展名 → 图标名映射
_EXT_ICON: dict[str, str] = {
    ".collection": "layer",
    ".input_binding": "input",
    ".lua": "code",
    ".json": "struct",
    ".md": "code",
    ".gitignore": "unused",
    ".cart": "struct",
}

# 目录名 → 图标名映射
_DIR_ICON: dict[str, str] = {
    "input": "input",
    "res": "dependency",
}


def _icon_for_file(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    # .gitignore 没有扩展名，单独处理
    if name.startswith("."):
        return _EXT_ICON.get(name, "unused")
    return _EXT_ICON.get(ext, "file")


def _icon_for_dir(name: str) -> str:
    return _DIR_ICON.get(name.lower(), "folder")


class AssetsItem(QStandardItem):
    """资源树节点，存储图标名以便主题切换时重建"""

    def __init__(self, label: str, icon_name: str, abs_path: str = ""):
        super().__init__(label)
        self._icon_name = icon_name
        self._abs_path = abs_path
        self.setIcon(get_icon(icon_name))
        self.setEditable(False)
        if abs_path:
            self.setToolTip(abs_path)

    def refresh_icon(self):
        self.setIcon(get_icon(self._icon_name))


class AssetsFsModel(QStandardItemModel):
    """
    资源面板数据模型。

    空状态（未打开项目）时显示占位提示；
    打开项目后扫描磁盘目录填充树。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["名称"])
        self._project_root: str = ""
        self._show_placeholder()

    # ── 公开 API ──────────────────────────────

    def load_from_root(self, project_root: str, project_name: str = ""):
        """
        扫描 project_root 目录，重建资源树。
        project_name 作为根节点显示名称；不传则用目录名。
        """
        self.clear()
        self.setHorizontalHeaderLabels(["名称"])
        self._project_root = os.path.abspath(project_root)

        display_name = project_name or os.path.basename(self._project_root)
        root = AssetsItem(display_name, "folder", self._project_root)
        self.appendRow(root)
        self._populate(root, self._project_root)

    def reload_icons(self):
        """主题切换后递归刷新所有节点图标"""
        self._refresh_icons(self.invisibleRootItem())

    # ── 内部方法 ──────────────────────────────

    def _show_placeholder(self):
        placeholder = QStandardItem("未打开项目")
        placeholder.setEditable(False)
        placeholder.setEnabled(False)
        self.appendRow(placeholder)

    def _populate(self, parent_item: AssetsItem, dir_path: str):
        """递归扫描目录，填充到 parent_item 下"""
        try:
            entries = sorted(os.scandir(dir_path), key=_sort_key)
        except PermissionError:
            return

        for entry in entries:
            # 跳过隐藏文件和 IDE 内部目录（.venv 等）
            if _should_skip(entry.name):
                continue

            if entry.is_dir(follow_symlinks=False):
                icon = _icon_for_dir(entry.name)
                item = AssetsItem(entry.name, icon, entry.path)
                parent_item.appendRow(item)
                self._populate(item, entry.path)
            else:
                icon = _icon_for_file(entry.name)
                item = AssetsItem(entry.name, icon, entry.path)
                parent_item.appendRow(item)

    def _refresh_icons(self, parent: QStandardItem):
        for row in range(parent.rowCount()):
            item = parent.child(row)
            if isinstance(item, AssetsItem):
                item.refresh_icon()
            self._refresh_icons(item)


# ── 辅助函数 ──────────────────────────────────

# 跳过这些目录/文件
_SKIP_NAMES = {".venv", ".git", ".idea", "__pycache__", ".DS_Store", "Thumbs.db"}
_SKIP_PREFIXES = (".",)   # 以 . 开头的隐藏文件/目录（.gitignore 除外）


def _should_skip(name: str) -> bool:
    if name in _SKIP_NAMES:
        return True
    # 保留 .gitignore，跳过其他隐藏文件
    if name.startswith(".") and name != ".gitignore":
        return True
    return False


def _sort_key(entry: os.DirEntry):
    """目录排在文件前，同类按名称字母序"""
    return (0 if entry.is_dir() else 1, entry.name.lower())