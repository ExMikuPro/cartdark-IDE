"""
CartDark IDE · project/scaffold.py
根据 IDE 对话框收集的配置，在磁盘上生成项目目录结构。
"""
from __future__ import annotations

import json
import os
import random
import uuid

from .schema import (
    CartProject, DisplayConfig, BootstrapConfig, BootstrapLayer,
    PackJson, PackMeta, PackIcon, PackHash, PackBuild, PackChunk,
)


# ──────────────────────────────────────────────
# 公开异常
# ──────────────────────────────────────────────

class ScaffoldError(Exception):
    """脚手架生成过程中的可预期错误"""


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def _generate_cart_id() -> str:
    """生成随机 cart_id，格式为 0x + 16位十六进制"""
    value = random.getrandbits(64)
    return f"0x{value:016X}"


def _generate_project_id() -> str:
    """生成 UUID v4 字符串作为 project.id"""
    return str(uuid.uuid4())


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

_INPUT_BINDING_TEMPLATE = """\
{{
  "format": "CART_INPUT_BINDING",
  "version": 1,
  "name": "{name}",
  "pin_triggers": [],
  "touch_triggers": [],
  "gamepad_triggers": []
}}
"""


_PINS_JSON_TEMPLATE = """\
{
  "format": "CART_BOARD_PINS",
  "version": 1,
  "name": "Board Template Pins",
  "pins": [
    { "id": "PA0",  "label": "PA0",  "tags": ["gpio", "exti"] },
    { "id": "PA1",  "label": "PA1",  "tags": ["gpio"] },
    { "id": "PB12", "label": "PB12", "tags": ["gpio"] },
    { "id": "PC13", "label": "PC13", "tags": ["gpio", "wkup"] }
  ]
}
"""

_COLLECTION_TEMPLATE = """\
{{
  "version": 1,
  "name": "{name}",
  "components": []
}}
"""


# ──────────────────────────────────────────────
# 模板构建器
# ──────────────────────────────────────────────

class _BlankBuilder:
    """blank 模板"""

    def __init__(self, config: dict):
        self.name: str = config["project_name"]
        self.root: str = os.path.join(config["location"], self.name)
        self.display: dict = config.get("display", {})
        self.options: dict = config.get("options", {})

    def build(self) -> str:
        """执行生成，返回项目根目录路径"""
        self._check_not_exists()
        _make_dirs(self.root)
        self._write_cart()
        self._write_pack_json()
        if self.options.get("create_readme", True):
            self._write_readme()
        if self.options.get("create_gitignore", True):
            self._write_gitignore()
        return self.root

    def _check_not_exists(self):
        if os.path.exists(self.root):
            raise ScaffoldError(f"目录已存在：{self.root}")

    def _write_cart(self):
        project = CartProject(
            name=self.name,
            template="blank",
            project_id=_generate_project_id(),
            display=DisplayConfig(
                width=self.display.get("width", 800),
                height=self.display.get("height", 480),
                format="ARGB8888",
            ),
        )
        path = os.path.join(self.root, f"{self.name}.cart")
        _write_json(path, project.to_dict())

    def _write_pack_json(self):
        pack = PackJson(
            meta=PackMeta(
                title=self.name,
                cart_id=_generate_cart_id(),
                entry="main/main.lua",
            ),
            icon=PackIcon(),
            hash=PackHash(),
            build=PackBuild(),
            chunks=[
                PackChunk(
                    type="MANF",
                    source="inline_meta",
                    name="meta/manifest.bin",
                ),
                PackChunk(
                    type="LUA",
                    glob="script/**/*.lua",
                    strip_prefix="script/",
                    name_prefix="main/",
                    exclude=["**/.DS_Store"],
                ),
                PackChunk(
                    type="RES",
                    glob="res/**/*",
                    strip_prefix="res/",
                    name_prefix="res/",
                    exclude=["**/.DS_Store", "**/*.psd"],
                ),
            ],
        )
        path = os.path.join(self.root, "pack.json")
        _write_json(path, pack.to_dict())

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
    """cartdark-os 模板，继承 blank 并额外创建子目录和文件"""

    def build(self) -> str:
        self._check_not_exists()

        # 创建所有目录
        _make_dirs(
            self.root,
            os.path.join(self.root, "board"),
            os.path.join(self.root, "input"),
            os.path.join(self.root, "main"),
            os.path.join(self.root, "res"),
            os.path.join(self.root, "script"),
        )

        self._write_cart()
        self._write_pack_json()

        # cartdark-os 专属文件
        self._write_input_binding()
        self._write_pins_json()
        self._write_collections()

        if self.options.get("create_readme", True):
            self._write_readme()
        if self.options.get("create_gitignore", True):
            self._write_gitignore()

        return self.root

    def _write_cart(self):
        project = CartProject(
            name=self.name,
            template="cartdark_os",
            project_id=_generate_project_id(),
            display=DisplayConfig(
                width=self.display.get("width", 800),
                height=self.display.get("height", 480),
                format="ARGB8888",
            ),
            bootstrap=BootstrapConfig(
                mode="LTDC",
                layers=[
                    BootstrapLayer(id=0, collection="/main/Layer0.collection",
                                   alpha=255, enabled=True),
                    BootstrapLayer(id=1, collection="/main/Layer1.collection",
                                   alpha=255, enabled=True),
                ],
            ),
        )
        path = os.path.join(self.root, f"{self.name}.cart")
        _write_json(path, project.to_dict())

    def _write_pack_json(self):
        pack = PackJson(
            meta=PackMeta(
                title=self.name,
                cart_id=_generate_cart_id(),
                entry="main/Layer0.collection",
            ),
            icon=PackIcon(),
            hash=PackHash(),
            build=PackBuild(),
            chunks=[
                PackChunk(
                    type="MANF",
                    source="inline_meta",
                    name="meta/manifest.bin",
                ),
                PackChunk(
                    type="RES",
                    glob="main/**/*",
                    strip_prefix="main/",
                    name_prefix="main/",
                    exclude=["**/.DS_Store"],
                ),
                PackChunk(
                    type="RES",
                    glob="input/**/*",
                    strip_prefix="input/",
                    name_prefix="input/",
                    exclude=["**/.DS_Store"],
                ),
                PackChunk(
                    type="RES",
                    glob="res/**/*",
                    strip_prefix="res/",
                    name_prefix="res/",
                    exclude=["**/.DS_Store", "**/*.psd"],
                ),
            ],
        )
        path = os.path.join(self.root, "pack.json")
        _write_json(path, pack.to_dict())

    def _write_input_binding(self):
        _write_text(
            os.path.join(self.root, "input", "game.input_binding"),
            _INPUT_BINDING_TEMPLATE.format(name=self.name),
        )

    def _write_pins_json(self):
        _write_text(
            os.path.join(self.root, "board", "pins.json"),
            _PINS_JSON_TEMPLATE,
        )

    def _write_collections(self):
        for layer_name in ("Layer0", "Layer1"):
            _write_text(
                os.path.join(self.root, "main", f"{layer_name}.collection"),
                _COLLECTION_TEMPLATE.format(name=layer_name),
            )


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
            "display": {"width": int, "height": int, "format": str},
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