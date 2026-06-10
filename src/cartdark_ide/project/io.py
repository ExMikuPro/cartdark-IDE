"""
CartDark IDE · project/io.py
项目文件的读写操作。
"""
from __future__ import annotations

import os

from .schema import CartProject, CartValidationError, read_cart_file


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
        return read_cart_file(cart_path, validate_files=False)
    except CartValidationError as e:
        raise ProjectLoadError(str(e)) from e


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
