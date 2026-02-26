"""
CartDark IDE · project/pack_sync.py
对 res/ 目录下文件的增删改，同步更新 pack.json 中对应的 chunk glob/path。

策略（第一版）：
  - pack.json 中 chunks 里每个带 glob 的条目，glob 形如 "res/**/*"
  - 删除/重命名/移动 res/ 下的文件或目录时，只更新 icon.path（如果匹配）
  - glob 是通配符，不需要逐文件维护；但 meta.entry 和 icon.path 是具体路径，需要更新
  - 对于精确 path 引用（icon.path、meta.entry），执行 rename/delete 时同步修改
"""
from __future__ import annotations

import json
import os
import re


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


def _is_under_res(project_root: str, abs_path: str) -> bool:
    res_root = os.path.join(project_root, "res") + os.sep
    return os.path.abspath(abs_path).startswith(os.path.abspath(res_root))


# ── 公开 API ──────────────────────────────────

def on_file_renamed(project_root: str, old_abs: str, new_abs: str) -> bool:
    """
    文件/目录重命名或移动后调用。
    只处理 res/ 下的路径。返回是否修改了 pack.json。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False
    if not _is_under_res(project_root, old_abs):
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

    if is_dir:
        for chunk in data.get("chunks", []):
            for field in ("glob", "strip_prefix", "name_prefix"):
                val = chunk.get(field, "")
                if val.startswith(old_prefix):
                    chunk[field] = new_prefix + val[len(old_prefix):]
                    changed = True

    # script chunk：更新 res 列表里的精确路径（文件或目录前缀）
    for chunk in data.get("chunks", []):
        if chunk.get("type") == "script":
            res_list = chunk.get("res", [])
            new_res = []
            for r in res_list:
                if r == old_rel:
                    new_res.append(new_rel)
                    changed = True
                elif r.startswith(old_prefix):
                    new_res.append(new_prefix + r[len(old_prefix):])
                    changed = True
                else:
                    new_res.append(r)
            chunk["res"] = new_res

    if changed:
        _save(pack_path, data)
    return changed


def on_file_deleted(project_root: str, abs_path: str) -> bool:
    """
    文件/目录删除后调用。
    处理 res/ 下的路径（icon/entry）以及所有目录的 script chunk。
    返回是否修改了 pack.json。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    data = _load(pack_path)
    changed = False
    rel = _rel(project_root, abs_path)

    # ── res/ 下：更新 icon.path / meta.entry ──
    if _is_under_res(project_root, abs_path):
        icon = data.get("icon", {})
        if icon.get("path") == rel:
            icon["path"] = ""
            changed = True

        meta = data.get("meta", {})
        if meta.get("entry") == rel:
            meta["entry"] = ""
            changed = True

    # ── 所有目录：从 script chunk res 列表移除 ──
    for chunk in data.get("chunks", []):
        if chunk.get("type") == "script":
            res_list = chunk.get("res", [])
            if rel in res_list:
                res_list.remove(rel)
                changed = True
            # 目录删除：移除所有以该路径开头的条目
            prefix = rel.rstrip("/") + "/"
            before = len(res_list)
            chunk["res"] = [r for r in res_list if not r.startswith(prefix)]
            if len(chunk["res"]) != before:
                changed = True

    if changed:
        _save(pack_path, data)
    return changed


def validate(project_root: str) -> list[str]:
    """
    校验 pack.json：
    - icon.path 文件是否存在
    - meta.entry 文件是否存在（在 res/ 下才检查）
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

    # icon
    icon_path = data.get("icon", {}).get("path", "")
    if icon_path:
        full = os.path.join(project_root, icon_path.replace("/", os.sep))
        if not os.path.isfile(full):
            issues.append(f"icon.path 文件不存在：{icon_path}")

    # meta.entry
    entry = data.get("meta", {}).get("entry", "")
    if entry:
        full = os.path.join(project_root, entry.replace("/", os.sep))
        if not os.path.isfile(full):
            issues.append(f"meta.entry 文件不存在：{entry}")

    # chunks glob
    for i, chunk in enumerate(data.get("chunks", [])):
        g = chunk.get("glob", "")
        if g:
            pattern = os.path.join(project_root, g.replace("/", os.sep))
            matches = glob_mod.glob(pattern, recursive=True)
            if not matches:
                issues.append(f"chunks[{i}] glob 未匹配到任何文件：{g}")

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
    危险操作：扫描 res/ 目录，重新生成 pack.json 中的 RES chunk。
    只替换 type==RES 且 glob 以 res/ 开头的 chunk。
    返回是否成功。
    """
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    res_dir = os.path.join(project_root, "res")
    if not os.path.isdir(res_dir):
        return False

    try:
        data = _load(pack_path)
        # 找到并替换 res chunk
        for chunk in data.get("chunks", []):
            if chunk.get("type") == "RES" and chunk.get("glob", "").startswith("res/"):
                chunk["glob"] = "res/**/*"
                chunk["strip_prefix"] = "res/"
                chunk["name_prefix"] = "res/"
                chunk["exclude"] = ["**/.DS_Store", "**/*.psd"]
        _save(pack_path, data)
        return True
    except Exception:
        return False


def add_script_to_pack(project_root: str, abs_path: str) -> bool:
    """
    把脚本文件加入 pack.json 的 type==script chunk 的 res 列表。
    如果不存在该 chunk，自动创建一个。
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

    # 找 type == "script" 的 chunk
    script_chunk = None
    for chunk in data.get("chunks", []):
        if chunk.get("type") == "script":
            script_chunk = chunk
            break

    if script_chunk is None:
        # 自动创建，插在 MANF 之后（第二位）
        script_chunk = {
            "type": "script",
            "compress": "none",
            "source": "inline_meta",
            "res": [],
            "exclude": ["**/.DS_Store"]
        }
        chunks = data.setdefault("chunks", [])
        # 找 MANF 的位置
        insert_pos = 1
        for i, c in enumerate(chunks):
            if c.get("type") == "MANF":
                insert_pos = i + 1
                break
        chunks.insert(insert_pos, script_chunk)

    # 加入 res 列表（去重）
    res_list = script_chunk.setdefault("res", [])
    if rel not in res_list:
        res_list.append(rel)

    try:
        _save(pack_path, data)
        return True
    except Exception:
        return False


def remove_script_from_pack(project_root: str, abs_path: str) -> bool:
    """从 pack.json 的 script chunk res 列表中移除指定脚本"""
    pack_path = _find_pack_json(project_root)
    if not pack_path:
        return False

    rel = _rel(project_root, abs_path)

    try:
        data = _load(pack_path)
        changed = False
        for chunk in data.get("chunks", []):
            if chunk.get("type") == "script":
                res_list = chunk.get("res", [])
                if rel in res_list:
                    res_list.remove(rel)
                    changed = True
        if changed:
            _save(pack_path, data)
        return changed
    except Exception:
        return False