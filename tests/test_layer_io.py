from __future__ import annotations

import json
import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.cartdark_ide.editors.editor2d.editor import Editor2D
from src.cartdark_ide.editors.editor2d.layer_io import LayerFileError, load_layer
from src.cartdark_ide.editors.cart_editor import CartEditor
from src.cartdark_ide.project.scaffold import create_project
from src.cartdark_ide.project.schema import read_cart_file


class LayerIoTests(unittest.TestCase):
    def test_scaffold_writes_default_cart_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp, template="cartdark_os")
            cart_path = os.path.join(root, "sample_cart.cart")
            icon_path = os.path.join(root, "assets", "app_icon.png")
            cart = read_cart_file(cart_path, validate_files=True)

            self.assertTrue(os.path.isfile(os.path.join(root, "scripts", "main.lua")))
            self.assertTrue(os.path.isfile(os.path.join(root, "layers", "default.layer")))
            self.assertTrue(os.path.isfile(icon_path))
            self.assertEqual(cart.platforms.cartdark_os.app_icon, "assets/app_icon.png")
            self.assertEqual(_read_png_size(icon_path), (200, 200))

    def test_cart_editor_save_preserves_project_id(self) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp, template="cartdark_os")
            cart_path = os.path.join(root, "sample_cart.cart")
            before = read_cart_file(cart_path, validate_files=True).project.id
            editor = CartEditor(cart_path)

            saved = editor.save()
            after = read_cart_file(cart_path, validate_files=True).project.id

        self.assertTrue(saved)
        self.assertEqual(after, before)
        editor.deleteLater()
        app.processEvents()

    def test_scaffold_writes_default_layer_canvas_from_cart_display(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp)
            cart = read_cart_file(os.path.join(root, "sample_cart.cart"), validate_files=True)
            layer = _read_json(os.path.join(root, "layers", "default.layer"))

        self.assertEqual(layer["canvas"]["width"], cart.display.width)
        self.assertEqual(layer["canvas"]["height"], cart.display.height)

    def test_missing_canvas_width_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_layer(tmp, {"canvas": {"height": 480}, "node": []})
            with self.assertRaisesRegex(LayerFileError, "canvas.width"):
                load_layer(path)

    def test_missing_canvas_height_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_layer(tmp, {"canvas": {"width": 800}, "node": []})
            with self.assertRaisesRegex(LayerFileError, "canvas.height"):
                load_layer(path)

    def test_empty_canvas_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_layer(tmp, {"canvas": {}, "node": []})
            with self.assertRaisesRegex(LayerFileError, "canvas.width"):
                load_layer(path)

    def test_valid_empty_node_layer_opens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_layer(
                tmp,
                {"canvas": {"width": 320, "height": 240}, "node": []},
            )
            result = load_layer(path)

        self.assertEqual(result.scene.canvas_width, 320)
        self.assertEqual(result.scene.canvas_height, 240)
        self.assertEqual(result.scene.nodes, [])

    def test_editor_uses_layer_canvas_size(self) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp)
            cart_path = os.path.join(root, "sample_cart.cart")
            cart = read_cart_file(cart_path, validate_files=False)
            layer_path = os.path.join(root, "layers", "default.layer")
            with open(layer_path, "w", encoding="utf-8") as f:
                json.dump({"canvas": {"width": 320, "height": 240}, "node": []}, f)

            editor = Editor2D(layer_path, project_root=root, cart_project=cart)

        self.assertEqual(editor._scene.canvas_width, 320)
        self.assertEqual(editor._scene.canvas_height, 240)
        editor.deleteLater()
        app.processEvents()


def _create_project(tmp: str, template: str = "blank") -> str:
    return create_project(
        {
            "template": template,
            "project_name": "sample_cart",
            "location": tmp,
            "options": {"create_readme": False, "create_gitignore": False},
        }
    )


def _write_layer(tmp: str, data: dict) -> str:
    path = os.path.join(tmp, "test.layer")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_png_size(path: str) -> tuple[int, int]:
    with open(path, "rb") as f:
        header = f.read(24)
    if not header.startswith(b"\x89PNG\r\n\x1a\n") or len(header) < 24:
        raise AssertionError(f"not a PNG file: {path}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


if __name__ == "__main__":
    unittest.main()
