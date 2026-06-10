"""
CartDark IDE · project/pack_sync.py
维护 XHGC_PACK v1.1 的 pack.json 输入规则。
"""
from __future__ import annotations

import json
import os
import re
from fnmatch import fnmatch


class PackSyncError(Exception):
    pass


def _find_pack_json(project_root: str) -> str | None:
    p = os.path.join(project_root, "pack.json")
    return p if os.path.isfile(p) else None


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _rel(project_root: str, abs_path: str) -> str:
    """abs_path 转相对于 project_root 的路径，使用 / 分隔符"""
    return os.path.relpath(abs_path, project_root).replace(os.sep, "/")


def _project_path(project_root: str, rel_path: str) -> str:
    """把 pack.json 中的项目内路径转为文件系统路径。"""
    return os.path.join(project_root, rel_path.lstrip("/").replace("/", os.sep))


def _pack_path_for_match(project_root: str, abs_path: str, chunk: dict) -> str:
    rel = _rel(project_root, abs_path)
    strip_prefix = chunk.get("strip_prefix")
    if strip_prefix is not None:
        prefix = strip_prefix.strip("/")
        if prefix:
            prefix += "/"
        if prefix and rel.startswith(prefix):
            rel = rel[len(prefix):]
    name_prefix = chunk.get("name_prefix", "")
    return f"{name_prefix}{rel}"


def _is_excluded(project_root: str, abs_path: str, excludes: list) -> bool:
    rel = _rel(project_root, abs_path)
    return any(
        fnmatch(rel, pattern) or fnmatch(os.path.basename(rel), pattern)
        for pattern in excludes
    )


# ── 公开 API ──────────────────────────────────

def on_file_renamed(project_root: str, old_abs: str, new_abs: str) -> bool:
    """
    文件/目录重命名或移动后调用。
    同步 pack.json 中的具体路径和 chunk 规则路径。返回是否修改了 pack.json。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    data = _load(pack_path)
    changed = False

    old_rel = _rel(project_root, old_abs)
    new_rel = _rel(project_root, new_abs)

    # icon.path
    icon = data.get("icon", {})
    if icon.get("path") == old_rel:
        icon["path"] = new_rel
        changed = True

    # meta.entry
    meta = data.get("meta", {})
    if meta.get("entry") == old_rel:
        meta["entry"] = new_rel
        changed = True

    # 目录重命名：更新所有以 old_rel/ 开头的 chunk strip_prefix / name_prefix / glob
    old_prefix = old_rel.rstrip("/") + "/"
    new_prefix = new_rel.rstrip("/") + "/"
    is_dir = os.path.isdir(new_abs)  # 重命名后检查

    for chunk in data.get("chunks", []):
        for field in ("glob", "strip_prefix", "name_prefix"):
            val = chunk.get(field, "")
            if val == old_rel:
                chunk[field] = new_rel
                changed = True
            elif is_dir and val.startswith(old_prefix):
                chunk[field] = new_prefix + val[len(old_prefix):]
                changed = True
        excludes = chunk.get("exclude", [])
        if isinstance(excludes, list):
            new_excludes = []
            for pattern in excludes:
                if pattern == old_rel:
                    new_excludes.append(new_rel)
                    changed = True
                elif is_dir and isinstance(pattern, str) and pattern.startswith(old_prefix):
                    new_excludes.append(new_prefix + pattern[len(old_prefix):])
                    changed = True
                else:
                    new_excludes.append(pattern)
            chunk["exclude"] = new_excludes

    if changed:
        _save(pack_path, data)
    return changed


def on_file_deleted(project_root: str, abs_path: str) -> bool:
    """
    文件/目录删除后调用。
    清空已删除的 icon / entry，并移除指向该路径的精确 chunk glob。
    返回是否修改了 pack.json。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    data = _load(pack_path)
    changed = False
    rel = _rel(project_root, abs_path)

    icon = data.get("icon", {})
    if isinstance(icon, dict) and icon.get("path") == rel:
        icon["path"] = ""
        changed = True

    meta = data.get("meta", {})
    if isinstance(meta, dict) and meta.get("entry") == rel:
        meta["entry"] = ""
        changed = True

    prefix = rel.rstrip("/") + "/"
    for chunk in data.get("chunks", []):
        glob_value = chunk.get("glob", "")
        if glob_value == rel or glob_value.startswith(prefix):
            chunk["glob"] = ""
            changed = True
        excludes = chunk.get("exclude", [])
        if isinstance(excludes, list):
            before = len(excludes)
            chunk["exclude"] = [
                item for item in excludes
                if item != rel and not (isinstance(item, str) and item.startswith(prefix))
            ]
            if len(chunk["exclude"]) != before:
                changed = True

    if changed:
        _save(pack_path, data)
    return changed


def validate(project_root: str) -> list[str]:
    """
    校验 pack.json：
    - v1.1 顶层格式与版本
    - icon.path 文件是否存在
    - meta.entry 文件是否存在并可由 chunks 输出集合匹配
    - chunks 中 glob 是否能匹配到至少一个文件
    返回问题列表（空列表表示无问题）。
    """
    import glob as glob_mod

    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return ["pack.json 不存在"]

    try:
        data = _load(pack_path)
    except Exception as e:
        return [f"pack.json 解析失败：{e}"]

    issues = []

    if data.get("format") != "XHGC_PACK":
        issues.append("format 必须为 XHGC_PACK")
    if data.get("pack_version") != 1:
        issues.append("pack_version 必须为 1")
    if "version" in data:
        issues.append("pack.json 顶层不应使用 version，请使用 pack_version")
    build = data.get("build", {})
    if isinstance(build, dict) and "include" in build:
        issues.append("build.include 已废弃，请使用 chunks")

    # icon
    icon = data.get("icon", {})
    if not isinstance(icon, dict):
        icon = {}
        issues.append("icon 必须为对象")
    icon_path = icon.get("path", "")
    if not icon_path:
        issues.append("icon.path 不能为空")
    if icon.get("format") != "ARGB8888":
        issues.append("icon.format 必须为 ARGB8888")
    if icon.get("width") != 200:
        issues.append("icon.width 必须为 200")
    if icon.get("height") != 200:
        issues.append("icon.height 必须为 200")
    if icon_path:
        full = _project_path(project_root, icon_path)
        if not os.path.isfile(full):
            issues.append(f"icon.path 文件不存在：{icon_path}")

    # meta.entry
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        issues.append("meta 必须为对象")
    cart_id = meta.get("cart_id", "")
    if not cart_id:
        issues.append("meta.cart_id 不能为空")
    elif not re.fullmatch(r"0x[0-9A-Fa-f]{16}", cart_id):
        issues.append("meta.cart_id 必须为 0x + 16 位十六进制")
    entry = meta.get("entry", "")
    if not entry:
        issues.append("meta.entry 不能为空")
    if entry:
        full = _project_path(project_root, entry)
        if not os.path.isfile(full):
            issues.append(f"meta.entry 文件不存在：{entry}")

    # chunks glob
    chunks = data.get("chunks", [])
    if not isinstance(chunks, list):
        chunks = []
        issues.append("chunks 必须为数组")
    if not chunks:
        issues.append("chunks 不能为空")
    elif chunks[0].get("type") != "MANF":
        issues.append("chunks[0].type 必须为 MANF")

    entry_in_chunks = False
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            issues.append(f"chunks[{i}] 必须为对象")
            continue
        chunk_type = chunk.get("type", "")
        if chunk_type not in {"MANF", "LUA", "RES"}:
            issues.append(f"chunks[{i}].type 非法：{chunk_type}")
        g = chunk.get("glob", "")
        if g:
            pattern = _project_path(project_root, g)
            matches = glob_mod.glob(pattern, recursive=True)
            files = [
                m for m in matches
                if os.path.isfile(m) and not _is_excluded(project_root, m, chunk.get("exclude", []))
            ]
            if not files:
                issues.append(f"chunks[{i}] glob 未匹配到任何文件：{g}")
            if entry and any(
                _pack_path_for_match(project_root, m, chunk) == entry
                for m in files
            ):
                entry_in_chunks = True

    if entry and chunks and not entry_in_chunks:
        issues.append(f"meta.entry 未出现在 chunks 输出集合中：{entry}")

    return issues


def format_json(project_root: str) -> bool:
    """格式化 pack.json，返回是否成功"""
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False
    try:
        data = _load(pack_path)
        _save(pack_path, data)
        return True
    except Exception:
        return False


def regenerate_from_res(project_root: str) -> bool:
    """
    已弃用：旧模板曾从固定资源目录重建 RES chunk。
    XHGC_PACK v1.1 使用显式 chunks 规则，本函数不再自动生成旧目录规则。
    """
    return False


def add_script_to_pack(project_root: str, abs_path: str) -> bool:
    """
    把 Lua 脚本文件加入 XHGC_PACK v1.1 的 LUA chunk。
    如果不存在对应 chunk，自动创建一个精确 glob 的 LUA chunk。
    返回是否成功。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    rel = _rel(project_root, abs_path)

    try:
        data = _load(pack_path)
    except Exception:
        return False

    lua_chunk = None
    for chunk in data.get("chunks", []):
        if chunk.get("type") == "LUA" and chunk.get("glob") == rel:
            lua_chunk = chunk
            break

    if lua_chunk is None:
        # 自动创建，插在 MANF 之后（第二位）
        lua_chunk = {
            "type": "LUA",
            "glob": rel,
            "name_prefix": "",
            "compress": "none",
            "exclude": ["**/.DS_Store"],
            "order": "lex",
        }
        chunks = data.setdefault("chunks", [])
        # 找 MANF 的位置
        insert_pos = 1
        for i, c in enumerate(chunks):
            if c.get("type") == "MANF":
                insert_pos = i + 1
                break
        chunks.insert(insert_pos, lua_chunk)

    try:
        _save(pack_path, data)
        return True
    except Exception:
        return False


def remove_script_from_pack(project_root: str, abs_path: str) -> bool:
    """从 pack.json 的 LUA chunk 中移除指定脚本的精确 glob"""
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    rel = _rel(project_root, abs_path)

    try:
        data = _load(pack_path)
        changed = False
        chunks = []
        for chunk in data.get("chunks", []):
            if chunk.get("type") == "LUA" and chunk.get("glob") == rel:
                changed = True
                continue
            chunks.append(chunk)
        if changed:
            data["chunks"] = chunks
            _save(pack_path, data)
        return changed
    except Exception:
        return False
