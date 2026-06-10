"""
CartDark IDE · project/scaffold.py
根据 IDE 对话框收集的配置，在磁盘上生成项目目录结构。
"""
from __future__ import annotations

import json
import os
import random
import shutil

from .schema import (
    create_default_cart_project, generate_project_id,
    PackJson, PackMeta, PackIcon, PackHash, PackBuild, PackChunk,
)


# ──────────────────────────────────────────────
# 公开异常
# ──────────────────────────────────────────────

class ScaffoldError(Exception):
    """脚手架生成过程中的可预期错误"""


_DEFAULT_APP_ICON_TEMPLATE = os.path.join(
    os.path.dirname(__file__),
    "templates",
    "cart",
    "default_app_icon.png",
)


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def _generate_cart_id() -> str:
    """生成随机 cart_id，格式为 0x + 16位十六进制"""
    value = random.getrandbits(64)
    return f"0x{value:016X}"


def _generate_project_id() -> str:
    """生成随机 64-bit project.id。"""
    return generate_project_id()


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _make_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


# ──────────────────────────────────────────────
# 文件内容模板
# ──────────────────────────────────────────────

_README_TEMPLATE = """\
# {name}

A CartDark project.

## 构建

使用 CartDark IDE 打开 `{name}.cart` 文件。
"""

_GITIGNORE_TEMPLATE = """\
# 构建输出
*.cart.bin
*.pack.lock.json
build/
dist/

# 系统文件
.DS_Store
Thumbs.db

# IDE 本地配置
.cartdark/local/
"""

_MAIN_LUA_TEMPLATE = """\
function init(self)
end

function update(self, dt)
end
"""

# ──────────────────────────────────────────────
# 模板构建器
# ──────────────────────────────────────────────

class _BlankBuilder:
    """blank 模板"""

    def __init__(self, config: dict):
        self.name: str = config["project_name"]
        self.root: str = os.path.join(config["location"], self.name)
        self.options: dict = config.get("options", {})
        self._cart_project = None

    def build(self) -> str:
        """执行生成，返回项目根目录路径"""
        self._check_not_exists()
        _make_dirs(
            self.root,
            os.path.join(self.root, "assets"),
            os.path.join(self.root, "layers"),
            os.path.join(self.root, "scripts"),
        )
        self._write_cart()
        self._write_pack_json()
        self._write_icon()
        self._write_scripts()
        self._write_layers()
        if self.options.get("create_readme", True):
            self._write_readme()
        if self.options.get("create_gitignore", True):
            self._write_gitignore()
        return self.root

    def _check_not_exists(self):
        if os.path.exists(self.root):
            raise ScaffoldError(f"目录已存在：{self.root}")

    def _write_cart(self):
        project = create_default_cart_project()
        project.project.id = _generate_project_id()
        self._cart_project = project
        path = os.path.join(self.root, f"{self.name}.cart")
        _write_json(path, project.to_dict())

    def _write_pack_json(self):
        pack = PackJson(
            meta=PackMeta(
                title="My Cart",
                title_zh="我的卡带",
                publisher="CartDark",
                cart_id=_generate_cart_id(),
                entry="scripts/main.lua",
                min_fw="0.1.0",
                id=f"com.cartdark.{self.name}",
                description={
                    "default": "A CartDark application.",
                    "zh-CN": "一个 CartDark 应用。",
                },
                tags=["cartdark"],
                author={
                    "name": "CartDark",
                    "contact": "",
                },
            ),
            icon=PackIcon(path="assets/app_icon.png"),
            hash=PackHash(),
            build=PackBuild(),
            chunks=[
                PackChunk(
                    type="MANF",
                    source="inline_meta",
                    name="meta/manifest.json",
                ),
                PackChunk(
                    type="LUA",
                    glob="scripts/**/*.lua",
                    name_prefix="",
                    compress="none",
                    exclude=["**/.DS_Store"],
                    order="lex",
                ),
                PackChunk(
                    type="RES",
                    glob="layers/**/*.layer",
                    name_prefix="",
                    compress="none",
                    exclude=["**/.DS_Store"],
                    order="lex",
                ),
            ],
        )
        path = os.path.join(self.root, "pack.json")
        _write_json(path, pack.to_dict())

    def _write_icon(self):
        target = os.path.join(self.root, "assets", "app_icon.png")
        if os.path.exists(target):
            raise ScaffoldError(f"文件已存在：{target}")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(_DEFAULT_APP_ICON_TEMPLATE, target)

    def _write_scripts(self):
        _write_text(os.path.join(self.root, "scripts", "main.lua"), _MAIN_LUA_TEMPLATE)

    def _write_layers(self):
        project = self._cart_project or create_default_cart_project()
        default_layer = {
            "canvas": {
                "width": project.display.width,
                "height": project.display.height,
            },
            "node": [],
        }
        _write_json(os.path.join(self.root, "layers", "default.layer"), default_layer)

    def _write_readme(self):
        _write_text(
            os.path.join(self.root, "README.md"),
            _README_TEMPLATE.format(name=self.name),
        )

    def _write_gitignore(self):
        _write_text(
            os.path.join(self.root, ".gitignore"),
            _GITIGNORE_TEMPLATE,
        )


class _CartdarkOsBuilder(_BlankBuilder):
    """cartdark-os 最小模板"""

    def _write_cart(self):
        project = create_default_cart_project()
        project.project.id = _generate_project_id()
        self._cart_project = project
        path = os.path.join(self.root, f"{self.name}.cart")
        _write_json(path, project.to_dict())

    def _write_pack_json(self):
        pack = {
            "format": "XHGC_PACK",
            "pack_version": 1,
            "meta": {
                "title": "My Cart",
                "title_zh": "我的卡带",
                "publisher": "CartDark",
                "version": "0.1.0",
                "cart_id": _generate_cart_id(),
                "entry": "scripts/main.lua",
                "min_fw": "0.1.0",
                "id": f"com.cartdark.{self.name}",
                "description": {
                    "default": "A CartDark application.",
                    "zh-CN": "一个 CartDark 应用。",
                },
                "category": "app",
                "tags": ["cartdark"],
                "author": {
                    "name": "CartDark",
                    "contact": "",
                },
            },
            "icon": {
                "path": "assets/app_icon.png",
                "format": "ARGB8888",
                "width": 200,
                "height": 200,
                "preprocess": {
                    "mode": "contain",
                    "background": "#000000",
                    "resample": "lanczos",
                },
            },
            "hash": {
                "header_crc32": True,
                "image_crc32": False,
                "per_chunk_crc32": False,
                "per_file_crc32": False,
            },
            "build": {
                "alignment_bytes": 4096,
                "deterministic": True,
                "fail_on_conflict": True,
            },
            "chunks": [
                {
                    "type": "MANF",
                    "source": "inline_meta",
                    "name": "meta/manifest.json",
                },
                {
                    "type": "LUA",
                    "glob": "scripts/**/*.lua",
                    "name_prefix": "",
                    "compress": "none",
                    "exclude": ["**/.DS_Store"],
                    "order": "lex",
                },
                {
                    "type": "RES",
                    "glob": "layers/**/*.layer",
                    "name_prefix": "",
                    "compress": "none",
                    "exclude": ["**/.DS_Store"],
                    "order": "lex",
                },
            ],
        }
        path = os.path.join(self.root, "pack.json")
        _write_json(path, pack)


# ──────────────────────────────────────────────
# 公开入口
# ──────────────────────────────────────────────

_BUILDERS = {
    "blank": _BlankBuilder,
    "cartdark_os": _CartdarkOsBuilder,
}


def create_project(config: dict) -> str:
    """
    根据 NewProjectDialog 传来的 config 字典在磁盘上创建项目。

    参数
    ----
    config : dict
        {
            "template": "blank" | "cartdark_os",
            "project_name": str,
            "location": str,
            "options": {
                "create_readme": bool,
                "create_gitignore": bool,
                "open_after_creation": bool,
            }
        }

    返回
    ----
    str : 创建成功后的项目根目录绝对路径

    异常
    ----
    ScaffoldError : 可预期的创建错误（目录已存在、权限不足等）
    """
    template = config.get("template", "blank")
    builder_cls = _BUILDERS.get(template)
    if builder_cls is None:
        raise ScaffoldError(f"未知模板：{template}")

    try:
        return builder_cls(config).build()
    except ScaffoldError:
        raise
    except OSError as e:
        raise ScaffoldError(f"文件系统错误：{e}") from e
