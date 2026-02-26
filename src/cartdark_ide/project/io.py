"""
CartDark IDE · project/io.py
项目文件的读写操作。
"""
from __future__ import annotations

import json
import os

from .schema import CartProject, DisplayConfig, BootstrapConfig, BootstrapLayer


class ProjectLoadError(Exception):
    """项目加载失败"""


def load_cart(cart_path: str) -> CartProject:
    """
    读取 .cart 文件，返回 CartProject。

    参数
    ----
    cart_path : .cart 文件的绝对路径

    异常
    ----
    ProjectLoadError : 文件不存在、格式错误等
    """
    if not os.path.isfile(cart_path):
        raise ProjectLoadError(f"文件不存在：{cart_path}")

    try:
        with open(cart_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ProjectLoadError(f"无法读取 .cart 文件：{e}") from e

    try:
        project_info = data.get("project", {})
        display_data = data.get("display", {})
        bootstrap_data = data.get("bootstrap")

        display = DisplayConfig(
            width=display_data.get("width", 800),
            height=display_data.get("height", 480),
            format=display_data.get("format", "ARGB8888"),
        )

        bootstrap = None
        if bootstrap_data:
            # 优先读新格式 bootstrap.layers
            if "layers" in bootstrap_data:
                layers = []
                for l in bootstrap_data["layers"]:
                    layers.append(BootstrapLayer(
                        id=l.get("id", 0),
                        collection=l.get("collection", ""),
                        alpha=l.get("alpha", 255),
                        enabled=l.get("enabled", True),
                    ))
                bootstrap = BootstrapConfig(
                    mode=bootstrap_data.get("mode", "LTDC"),
                    layers=layers,
                )
            else:
                # fallback：旧格式 bootstrap.main_collection → 映射为 layer0
                main_col = bootstrap_data.get("main_collection", "/main/Layer0.collection")
                bootstrap = BootstrapConfig(
                    mode="LTDC",
                    layers=[
                        BootstrapLayer(id=0, collection=main_col,
                                       alpha=255, enabled=True),
                        BootstrapLayer(id=1, collection="/main/Layer1.collection",
                                       alpha=255, enabled=True),
                    ],
                )

        return CartProject(
            format=data.get("format", "CART_PROJECT"),
            version=data.get("version", 1),
            name=project_info.get("name", os.path.basename(os.path.dirname(cart_path))),
            template=project_info.get("template", "blank"),
            project_id=project_info.get("id", ""),
            display=display,
            bootstrap=bootstrap,
        )
    except Exception as e:
        raise ProjectLoadError(f".cart 文件结构异常：{e}") from e


def find_cart_file(project_root: str) -> str:
    """
    在项目根目录中找到 .cart 文件，返回其绝对路径。
    如果找不到或有多个则抛出 ProjectLoadError。
    """
    if not os.path.isdir(project_root):
        raise ProjectLoadError(f"不是有效目录：{project_root}")

    cart_files = [
        f for f in os.listdir(project_root)
        if f.endswith(".cart") and os.path.isfile(os.path.join(project_root, f))
    ]

    if not cart_files:
        raise ProjectLoadError(f"目录中未找到 .cart 文件：{project_root}")
    if len(cart_files) > 1:
        raise ProjectLoadError(f"目录中存在多个 .cart 文件：{cart_files}")

    return os.path.join(project_root, cart_files[0])