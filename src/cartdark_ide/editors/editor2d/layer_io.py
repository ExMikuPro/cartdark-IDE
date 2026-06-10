"""Read and write CartDark `.layer` JSON files."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

from .scene import Node2D, Scene2D


class LayerFileError(Exception):
    """Layer file loading or saving failed."""


@dataclass
class LayerLoadResult:
    scene: Scene2D
    message: str = ""
    missing: bool = False


def load_layer(
    path: str,
    *,
    default_width: int = 800,
    default_height: int = 480,
) -> LayerLoadResult:
    default_width, default_height = _normalize_canvas_size(
        default_width, default_height
    )
    if not path:
        return LayerLoadResult(
            Scene2D(canvas_width=default_width, canvas_height=default_height),
            "bootstrap.layer1 为空，已创建空白编辑状态；保存前需要选择 .layer 路径。",
            missing=True,
        )
    if not os.path.isfile(path):
        return LayerLoadResult(
            Scene2D(canvas_width=default_width, canvas_height=default_height),
            f".layer 文件不存在，已创建空白编辑状态：{path}",
            missing=True,
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise LayerFileError(f".layer 文件解析失败：{e}") from e
    except OSError as e:
        raise LayerFileError(f"无法读取 .layer 文件：{e}") from e

    return LayerLoadResult(_scene_from_layer_dict(data))


def save_layer(path: str, scene: Scene2D) -> None:
    if not path:
        raise LayerFileError("bootstrap.layer1 为空，无法保存；请选择 .layer 文件路径。")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_scene_to_layer_dict(scene), f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        raise LayerFileError(f"保存 .layer 失败：{e}") from e


def _scene_from_layer_dict(data: Any) -> Scene2D:
    if not isinstance(data, dict):
        raise LayerFileError(".layer 根节点必须是 JSON Object")

    canvas = data.get("canvas")
    if not isinstance(canvas, dict):
        raise LayerFileError(".layer canvas 必须存在且必须是 JSON Object")
    canvas_width = _required_positive_int(canvas, "width", ".layer canvas.width")
    canvas_height = _required_positive_int(canvas, "height", ".layer canvas.height")

    nodes_data = data.get("node")
    if not isinstance(nodes_data, list):
        raise LayerFileError(".layer node 必须存在且必须是数组")

    nodes: list[Node2D] = []
    for index, item in enumerate(nodes_data, start=1):
        nodes.append(_node_from_layer_dict(item, index))
    return Scene2D(nodes=nodes, canvas_width=canvas_width, canvas_height=canvas_height)


def _node_from_layer_dict(data: Any, index: int) -> Node2D:
    field = f".layer node[{index}]"
    if not isinstance(data, dict):
        raise LayerFileError(f"{field} 必须是 JSON Object")

    node_id = _required_string(data, "id", f"{field}.id")
    node_type = _required_string(data, "type", f"{field}.type")
    if node_type != "image":
        raise LayerFileError(f"{field}.type 当前仅支持 image：{node_type}")
    name = _required_string(data, "name", f"{field}.name")
    path = _required_string(data, "path", f"{field}.path")

    position = data.get("position")
    if not isinstance(position, dict):
        raise LayerFileError(f"{field}.position 必须存在且必须是 JSON Object")
    x = _required_number(position, "x", f"{field}.position.x")
    y = _required_number(position, "y", f"{field}.position.y")

    return Node2D(id=node_id, type=node_type, name=name, path=path, x=x, y=y)


def _scene_to_layer_dict(scene: Scene2D) -> dict[str, Any]:
    width, height = _normalize_canvas_size(scene.canvas_width, scene.canvas_height)
    return {
        "canvas": {
            "width": width,
            "height": height,
        },
        "node": [node.to_dict() for node in scene.nodes],
    }


def _normalize_canvas_size(width: Any, height: Any) -> tuple[int, int]:
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        width = 800
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        height = 480
    return width, height


def _required_string(data: dict[str, Any], key: str, field_path: str) -> str:
    if key not in data:
        raise LayerFileError(f"{field_path} 必须存在")
    value = data[key]
    if not isinstance(value, str):
        raise LayerFileError(f"{field_path} 必须是字符串")
    return value


def _required_number(data: dict[str, Any], key: str, field_path: str) -> float:
    if key not in data:
        raise LayerFileError(f"{field_path} 必须存在")
    value = data[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise LayerFileError(f"{field_path} 必须是数字")
    return float(value)


def _required_positive_int(data: dict[str, Any], key: str, field_path: str) -> int:
    if key not in data:
        raise LayerFileError(f"{field_path} 必须存在")
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise LayerFileError(f"{field_path} 必须是正整数")
    return value
