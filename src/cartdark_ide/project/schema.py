"""
CartDark IDE · project/schema.py
项目数据结构定义（对应 .cart 文件和 pack.json v1.1）
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# .cart 文件结构
# ──────────────────────────────────────────────

@dataclass
class DisplayConfig:
    width: int = 800
    height: int = 480
    format: str = "ARGB8888"  # ARGB8888 / RGB888 / RGB565 / RGB555


@dataclass
class BootstrapLayer:
    id: int = 0
    collection: str = "/main/Layer0.collection"
    alpha: int = 255
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "collection": self.collection,
            "alpha": self.alpha,
            "enabled": self.enabled,
        }


@dataclass
class BootstrapConfig:
    mode: str = "LTDC"
    layers: list = field(default_factory=lambda: [
        BootstrapLayer(id=0, collection="/main/Layer0.collection"),
        BootstrapLayer(id=1, collection="/main/Layer1.collection"),
    ])

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "layers": [l.to_dict() for l in self.layers],
        }


@dataclass
class CartProject:
    """对应 .cart 文件的完整结构"""
    format: str = "CART_PROJECT"
    version: int = 1
    name: str = ""
    template: str = "blank"       # blank | cartdark_os
    project_id: str = ""          # UUID v4
    display: DisplayConfig = field(default_factory=DisplayConfig)
    bootstrap: Optional[BootstrapConfig] = None

    def to_dict(self) -> dict:
        d: dict = {
            "format": self.format,
            "version": self.version,
            "project": {
                "name": self.name,
                "template": self.template,
                "id": self.project_id,
            },
            "display": {
                "width": self.display.width,
                "height": self.display.height,
                "format": self.display.format,
            },
        }
        if self.bootstrap:
            d["bootstrap"] = self.bootstrap.to_dict()
        return d


# ──────────────────────────────────────────────
# pack.json v1.1 结构
# ──────────────────────────────────────────────

@dataclass
class PackMeta:
    title: str = ""
    version: str = "0.1.0"
    cart_id: str = ""             # "0x" + 16位十六进制，IDE 自动生成
    entry: str = "main/main.lua"
    title_zh: str = ""
    publisher: str = ""
    min_fw: str = ""
    id: str = ""                  # 反域名包名，可选
    description: Optional[dict] = None
    category: str = "app"
    tags: list = field(default_factory=list)
    author: Optional[dict] = None

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
    path: str = "res/icon.png"
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
    compress: str = "none"
    # MANF 专用
    source: Optional[str] = None
    name: Optional[str] = None
    # LUA / RES 专用
    glob: Optional[str] = None
    name_prefix: Optional[str] = None
    strip_prefix: Optional[str] = None
    exclude: list = field(default_factory=list)
    order: str = "lex"

    def to_dict(self) -> dict:
        d: dict = {"type": self.type, "compress": self.compress}
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
        if self.exclude:
            d["exclude"] = self.exclude
        if self.order != "lex":
            d["order"] = self.order
        return d


@dataclass
class PackJson:
    """对应 pack.json v1.1 的完整结构"""
    meta: PackMeta = field(default_factory=PackMeta)
    icon: PackIcon = field(default_factory=PackIcon)
    hash: PackHash = field(default_factory=PackHash)
    build: PackBuild = field(default_factory=PackBuild)
    chunks: list[PackChunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "format": "XHGC_PACK",
            "pack_version": 1,
            "meta": self.meta.to_dict(),
            "icon": self.icon.to_dict(),
            "hash": self.hash.to_dict(),
            "build": self.build.to_dict(),
            "chunks": [c.to_dict() for c in self.chunks],
        }