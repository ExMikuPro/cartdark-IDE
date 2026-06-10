"""Basic 2D scene model for the `.layer` editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


SUPPORTED_NODE_TYPES = {"image"}


def new_node_id() -> str:
    return "node_" + uuid.uuid4().hex[:8]


@dataclass
class Node2D:
    id: str = field(default_factory=new_node_id)
    type: str = "image"
    name: str = "Image"
    path: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 120.0
    height: float = 80.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node2D":
        position = data.get("position", {})
        node_type = str(data.get("type", "image"))
        if node_type not in SUPPORTED_NODE_TYPES:
            node_type = "image"
        return cls(
            id=str(data.get("id") or new_node_id()),
            name=str(data.get("name") or node_type.title()),
            type=node_type,
            path=str(data.get("path", "")),
            x=_number(position.get("x"), 0.0) if isinstance(position, dict) else 0.0,
            y=_number(position.get("y"), 0.0) if isinstance(position, dict) else 0.0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "position": {
                "x": self.x,
                "y": self.y,
            },
        }


@dataclass
class Scene2D:
    nodes: list[Node2D] = field(default_factory=list)
    canvas_width: int = 800
    canvas_height: int = 480

    def add_image(self) -> Node2D:
        index = len(self.nodes) + 1
        node = Node2D(id=f"node_{index:04d}", name=f"Image {index}")
        while self.by_id(node.id):
            index += 1
            node.id = f"node_{index:04d}"
            node.name = f"Image {index}"
        self.nodes.append(node)
        return node

    def remove(self, node: Node2D) -> None:
        self.nodes = [item for item in self.nodes if item.id != node.id]

    def by_id(self, node_id: str) -> Node2D | None:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
