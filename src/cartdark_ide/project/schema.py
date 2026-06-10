"""
CartDark IDE · project/schema.py
.cart 项目描述文件与 pack.json v1.1 数据结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
import secrets
import struct
from typing import Any


CART_PROJECT_FORMAT = "CART_PROJECT_v1.00"
SUPPORTED_CART_FORMATS = {CART_PROJECT_FORMAT}
PROJECT_ID_PATTERN = re.compile(r"^0x[0-9A-Fa-f]{16}$")


class CartValidationError(Exception):
    """`.cart` 文件结构或字段校验失败。"""


def generate_project_id() -> str:
    """生成随机 64-bit project.id，格式为 0x + 16 位十六进制。"""
    return f"0x{secrets.randbits(64):016X}"


def _project_path(project_root: str, rel_path: str) -> str:
    normalized = rel_path.replace("\\", "/")
    if os.path.isabs(normalized) or normalized.startswith("/"):
        raise CartValidationError(f"路径必须相对于项目根目录：{rel_path}")
    abs_path = os.path.abspath(os.path.join(project_root, normalized))
    root = os.path.abspath(project_root)
    if os.path.commonpath([root, abs_path]) != root:
        raise CartValidationError(f"路径不能指向项目根目录外：{rel_path}")
    return abs_path


def _require_object(data: Any, field_path: str) -> dict:
    if not isinstance(data, dict):
        raise CartValidationError(f"{field_path} 必须是 JSON Object")
    return data


def _require_string(data: dict, key: str, field_path: str) -> str:
    if key not in data:
        raise CartValidationError(f"{field_path} 必须存在")
    value = data[key]
    if not isinstance(value, str):
        raise CartValidationError(f"{field_path} 必须是字符串")
    return value


def _require_positive_int(data: dict, key: str, field_path: str) -> int:
    if key not in data:
        raise CartValidationError(f"{field_path} 必须存在")
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise CartValidationError(f"{field_path} 必须是正整数")
    return value


def _validate_project_file_path(
    project_root: str,
    rel_path: str,
    field_path: str,
    suffix: str,
    *,
    allow_empty: bool = False,
) -> None:
    if allow_empty and rel_path == "":
        return
    if not rel_path:
        raise CartValidationError(f"{field_path} 不能为空")
    if not rel_path.lower().endswith(suffix):
        raise CartValidationError(f"{field_path} 必须指向 {suffix} 文件：{rel_path}")
    _project_path(project_root, rel_path)


def _validate_icon(project_root: str, rel_path: str) -> None:
    full_path = _project_path(project_root, rel_path)
    if not os.path.isfile(full_path):
        raise CartValidationError(f"platforms.cartdark-os.app_icon 文件不存在：{rel_path}")
    size = _read_image_size(full_path)
    if size is None:
        raise CartValidationError(
            f"platforms.cartdark-os.app_icon 不是可识别的图像文件：{rel_path}"
        )
    width, height = size
    if width != 200 or height != 200:
        raise CartValidationError(
            "platforms.cartdark-os.app_icon 图标尺寸必须为 200x200，"
            f"当前为 {width}x{height}：{rel_path}"
        )


def _read_image_size(path: str) -> tuple[int, int] | None:
    with open(path, "rb") as f:
        header = f.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        if header.startswith(b"BM") and len(header) >= 26:
            return struct.unpack("<II", header[18:26])
        if header.startswith(b"\xff\xd8"):
            f.seek(2)
            while True:
                marker_start = f.read(1)
                if not marker_start:
                    return None
                if marker_start != b"\xff":
                    continue
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3",
                              b"\xc5", b"\xc6", b"\xc7", b"\xc9",
                              b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                    data = f.read(7)
                    if len(data) != 7:
                        return None
                    height, width = struct.unpack(">HH", data[3:7])
                    return width, height
                size_data = f.read(2)
                if len(size_data) != 2:
                    return None
                size = struct.unpack(">H", size_data)[0]
                if size < 2:
                    return None
                f.seek(size - 2, os.SEEK_CUR)
    return None


@dataclass
class CartBootstrap:
    entry: str = "scripts/main.lua"
    layer0: str = ""
    layer1: str = "layers/default.layer"

    def to_dict(self) -> dict:
        return {
            "entry": self.entry,
            "layer0": self.layer0,
            "layer1": self.layer1,
        }


@dataclass
class CartProjectInfo:
    id: str = field(default_factory=generate_project_id)
    title: str = "My Cart"
    title_zh: str = "我的卡带"
    version: str = "0.1.0"
    developer: str = "Developer Name"
    min_fw: str = "0.1.0"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "title_zh": self.title_zh,
            "version": self.version,
            "developer": self.developer,
            "min_fw": self.min_fw,
        }


@dataclass
class CartdarkOsPlatform:
    app_icon: str = "assets/app_icon.png"

    def to_dict(self) -> dict:
        return {"app_icon": self.app_icon}


@dataclass
class CartPlatforms:
    cartdark_os: CartdarkOsPlatform = field(default_factory=CartdarkOsPlatform)

    def to_dict(self) -> dict:
        return {"cartdark-os": self.cartdark_os.to_dict()}


@dataclass
class CartDisplay:
    width: int = 800
    height: int = 480

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
        }


@dataclass
class CartProject:
    """对应 `CART_PROJECT_v1.00` `.cart` 文件的完整结构。"""

    format: str = CART_PROJECT_FORMAT
    bootstrap: CartBootstrap = field(default_factory=CartBootstrap)
    project: CartProjectInfo = field(default_factory=CartProjectInfo)
    platforms: CartPlatforms = field(default_factory=CartPlatforms)
    display: CartDisplay = field(default_factory=CartDisplay)

    @property
    def name(self) -> str:
        """兼容旧 UI：项目显示名取 Launcher 默认标题。"""
        return self.project.title

    @property
    def project_id(self) -> str:
        return self.project.id

    def to_dict(self) -> dict:
        return {
            "format": self.format,
            "bootstrap": self.bootstrap.to_dict(),
            "project": self.project.to_dict(),
            "platforms": self.platforms.to_dict(),
            "display": self.display.to_dict(),
        }


def create_default_cart_project() -> CartProject:
    """创建新项目默认 `.cart` 数据，包含随机 project.id。"""
    return CartProject()


def cart_project_from_dict(data: dict) -> CartProject:
    validate_cart_data(data)
    bootstrap = data["bootstrap"]
    project = data["project"]
    cartdark_os = data["platforms"]["cartdark-os"]
    display = data["display"]
    return CartProject(
        format=data["format"],
        bootstrap=CartBootstrap(
            entry=bootstrap["entry"],
            layer0=bootstrap["layer0"],
            layer1=bootstrap["layer1"],
        ),
        project=CartProjectInfo(
            id=project["id"],
            title=project["title"],
            title_zh=project["title_zh"],
            version=project["version"],
            developer=project["developer"],
            min_fw=project["min_fw"],
        ),
        platforms=CartPlatforms(
            cartdark_os=CartdarkOsPlatform(app_icon=cartdark_os["app_icon"])
        ),
        display=CartDisplay(
            width=display["width"],
            height=display["height"],
        ),
    )


def read_cart_file(cart_path: str, *, validate_files: bool = True) -> CartProject:
    if not os.path.isfile(cart_path):
        raise CartValidationError(f"文件不存在：{cart_path}")
    try:
        with open(cart_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CartValidationError(f".cart 文件不是合法 JSON：{e}") from e
    except OSError as e:
        raise CartValidationError(f"无法读取 .cart 文件：{e}") from e
    project_root = os.path.dirname(os.path.abspath(cart_path))
    validate_cart_data(data, project_root if validate_files else None)
    return cart_project_from_dict(data)


def write_cart_file(cart_path: str, project: CartProject | dict) -> None:
    data = project.to_dict() if isinstance(project, CartProject) else project
    project_root = os.path.dirname(os.path.abspath(cart_path))
    validate_cart_data(data, project_root)
    with open(cart_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validate_cart_file(cart_path: str) -> list[str]:
    try:
        read_cart_file(cart_path, validate_files=True)
    except CartValidationError as e:
        return [str(e)]
    return []


def validate_cart_data(data: Any, project_root: str | None = None) -> None:
    root = _require_object(data, "根节点")

    format_value = _require_string(root, "format", "format")
    if format_value not in SUPPORTED_CART_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_CART_FORMATS))
        raise CartValidationError(
            f"format 不支持：{format_value}；当前支持：{supported}"
        )

    if "bootstrap" not in root:
        raise CartValidationError("bootstrap 必须存在")
    bootstrap = _require_object(root["bootstrap"], "bootstrap")
    entry = _require_string(bootstrap, "entry", "bootstrap.entry")
    layer0 = _require_string(bootstrap, "layer0", "bootstrap.layer0")
    layer1 = _require_string(bootstrap, "layer1", "bootstrap.layer1")

    if not entry.lower().endswith(".lua"):
        raise CartValidationError(f"bootstrap.entry 必须指向 .lua 文件：{entry}")
    if layer0 and not layer0.lower().endswith(".layer"):
        raise CartValidationError(f"bootstrap.layer0 必须指向 .layer 文件：{layer0}")
    if not layer1.lower().endswith(".layer"):
        raise CartValidationError(f"bootstrap.layer1 必须指向 .layer 文件：{layer1}")

    if "project" not in root:
        raise CartValidationError("project 必须存在")
    project = _require_object(root["project"], "project")
    project_id = _require_string(project, "id", "project.id")
    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise CartValidationError("project.id 必须符合 0x + 16 位十六进制")
    for key in ("title", "title_zh", "version", "developer", "min_fw"):
        _require_string(project, key, f"project.{key}")

    if "platforms" not in root:
        raise CartValidationError("platforms 必须存在")
    platforms = _require_object(root["platforms"], "platforms")
    if "cartdark-os" not in platforms:
        raise CartValidationError("platforms.cartdark-os 必须存在")
    cartdark_os = _require_object(platforms["cartdark-os"], "platforms.cartdark-os")
    app_icon = _require_string(
        cartdark_os, "app_icon", "platforms.cartdark-os.app_icon"
    )

    if "display" not in root:
        raise CartValidationError("display 必须存在")
    display = _require_object(root["display"], "display")
    _require_positive_int(display, "width", "display.width")
    _require_positive_int(display, "height", "display.height")

    if project_root:
        _validate_project_file_path(project_root, entry, "bootstrap.entry", ".lua")
        _validate_project_file_path(
            project_root, layer0, "bootstrap.layer0", ".layer", allow_empty=True
        )
        _validate_project_file_path(project_root, layer1, "bootstrap.layer1", ".layer")
        _validate_icon(project_root, app_icon)


# ──────────────────────────────────────────────
# pack.json v1.1 结构
# ──────────────────────────────────────────────

@dataclass
class PackMeta:
    title: str = ""
    version: str = "0.1.0"
    cart_id: str = ""             # "0x" + 16位十六进制，IDE 自动生成
    entry: str = "scripts/main.lua"
    title_zh: str = ""
    publisher: str = ""
    min_fw: str = ""
    id: str = ""                  # 反域名包名，可选
    description: dict | None = None
    category: str = "app"
    tags: list = field(default_factory=list)
    author: dict | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "title": self.title,
            "version": self.version,
            "cart_id": self.cart_id,
            "entry": self.entry,
        }
        if self.title_zh:
            d["title_zh"] = self.title_zh
        if self.publisher:
            d["publisher"] = self.publisher
        if self.min_fw:
            d["min_fw"] = self.min_fw
        if self.id:
            d["id"] = self.id
        if self.description:
            d["description"] = self.description
        if self.category != "app":
            d["category"] = self.category
        if self.tags:
            d["tags"] = self.tags
        if self.author:
            d["author"] = self.author
        return d


@dataclass
class PackIcon:
    path: str = "assets/app_icon.png"
    format: str = "ARGB8888"
    width: int = 200
    height: int = 200
    preprocess: dict = field(default_factory=lambda: {
        "mode": "contain",
        "background": "#000000",
        "resample": "lanczos"
    })

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "preprocess": self.preprocess,
        }


@dataclass
class PackHash:
    header_crc32: bool = True
    image_crc32: bool = False
    per_chunk_crc32: bool = False
    per_file_crc32: bool = False

    def to_dict(self) -> dict:
        return {
            "header_crc32": self.header_crc32,
            "image_crc32": self.image_crc32,
            "per_chunk_crc32": self.per_chunk_crc32,
            "per_file_crc32": self.per_file_crc32,
        }


@dataclass
class PackBuild:
    alignment_bytes: int = 4096
    deterministic: bool = True
    fail_on_conflict: bool = True

    def to_dict(self) -> dict:
        return {
            "alignment_bytes": self.alignment_bytes,
            "deterministic": self.deterministic,
            "fail_on_conflict": self.fail_on_conflict,
        }


@dataclass
class PackChunk:
    type: str = "RES"             # MANF | LUA | RES
    source: str | None = None
    name: str | None = None
    glob: str | None = None
    name_prefix: str | None = None
    strip_prefix: str | None = None
    compress: str = "none"
    exclude: list = field(default_factory=list)
    order: str = "lex"
    image_format: str | None = None
    image_preprocess: dict | None = None

    def to_dict(self) -> dict:
        d: dict = {"type": self.type}
        if self.source is not None:
            d["source"] = self.source
        if self.name is not None:
            d["name"] = self.name
        if self.glob is not None:
            d["glob"] = self.glob
        if self.name_prefix is not None:
            d["name_prefix"] = self.name_prefix
        if self.strip_prefix is not None:
            d["strip_prefix"] = self.strip_prefix
        if self.type != "MANF" or self.compress != "none":
            d["compress"] = self.compress
        if self.exclude:
            d["exclude"] = self.exclude
        if self.order != "lex":
            d["order"] = self.order
        if self.image_format is not None:
            d["image_format"] = self.image_format
        if self.image_preprocess is not None:
            d["image_preprocess"] = self.image_preprocess
        return d


@dataclass
class PackJson:
    """对应 pack.json v1.1 的完整结构。"""

    format: str = "XHGC_PACK"
    pack_version: int = 1
    meta: PackMeta = field(default_factory=PackMeta)
    icon: PackIcon = field(default_factory=PackIcon)
    hash: PackHash = field(default_factory=PackHash)
    build: PackBuild = field(default_factory=PackBuild)
    chunks: list[PackChunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "format": self.format,
            "pack_version": self.pack_version,
            "meta": self.meta.to_dict(),
            "icon": self.icon.to_dict(),
            "hash": self.hash.to_dict(),
            "build": self.build.to_dict(),
            "chunks": [c.to_dict() for c in self.chunks],
        }
