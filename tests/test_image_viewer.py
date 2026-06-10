from __future__ import annotations

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from src.cartdark_ide.editors.editor_host import EditorHost, make_editor
from src.cartdark_ide.editors.image_viewer import ImageViewerEditor, is_supported_image_path
from src.cartdark_ide.project.io import read_cart_file
from src.cartdark_ide.project.scaffold import create_project
from src.cartdark_ide.workspace.workspace import Workspace


class ImageViewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        self.app.processEvents()

    def test_png_file_is_recognized_as_image(self) -> None:
        self.assertTrue(is_supported_image_path("assets/app_icon.png"))

    def test_jpg_and_jpeg_files_are_recognized_as_images(self) -> None:
        self.assertTrue(is_supported_image_path("photo.jpg"))
        self.assertTrue(is_supported_image_path("photo.jpeg"))

    def test_non_image_file_does_not_open_image_preview_editor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "main.lua")
            _write_text(path, "function init(self)\nend\n")

            editor = make_editor(path, project_root=tmp)

        self.assertIsInstance(editor, EditorHost)
        self.assertNotIsInstance(editor, ImageViewerEditor)
        editor.deleteLater()

    def test_clicking_image_file_creates_image_preview_tab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "icon.png")
            _write_png(path, 32, 24)
            workspace = Workspace()
            workspace.set_project_root(tmp)

            workspace.open_file(path)

            editor = workspace._editors[os.path.abspath(path)]
            self.assertIsInstance(editor, ImageViewerEditor)
            self.assertIs(workspace._stack.currentWidget(), editor)
            workspace.deleteLater()

    def test_clicking_same_image_reuses_existing_tab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "icon.png")
            _write_png(path, 32, 24)
            workspace = Workspace()
            workspace.set_project_root(tmp)

            workspace.open_file(path)
            first_editor = workspace._editors[os.path.abspath(path)]
            workspace.open_file(path)

            self.assertEqual(len(workspace._editors), 1)
            self.assertIs(workspace._editors[os.path.abspath(path)], first_editor)
            workspace.deleteLater()

    def test_image_load_reads_correct_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "icon.png")
            _write_png(path, 64, 48)

            editor = ImageViewerEditor(path, project_root=tmp)

        self.assertEqual(editor.image_size, (64, 48))
        self.assertEqual(editor.error_message, "")
        editor.deleteLater()

    def test_damaged_image_shows_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "broken.png")
            with open(path, "wb") as f:
                f.write(b"not a valid png")

            editor = ImageViewerEditor(path, project_root=tmp)

        self.assertIn("图片解码失败", editor.error_message)
        editor.deleteLater()

    def test_app_icon_opens_and_reports_200_by_200(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp)
            icon_path = os.path.join(root, "assets", "app_icon.png")
            workspace = Workspace()
            workspace.set_project_root(root)

            workspace.open_file(icon_path)

            editor = workspace._editors[os.path.abspath(icon_path)]
            self.assertIsInstance(editor, ImageViewerEditor)
            self.assertEqual(editor.image_size, (200, 200))
            workspace.deleteLater()

    def test_opening_image_does_not_modify_cart_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp)
            cart_path = os.path.join(root, "sample_cart.cart")
            icon_path = os.path.join(root, "assets", "app_icon.png")
            before = _read_bytes(cart_path)
            workspace = Workspace()
            workspace.set_project_root(root)

            workspace.open_file(icon_path)

            self.assertEqual(_read_bytes(cart_path), before)
            workspace.deleteLater()

    def test_opening_image_does_not_modify_project_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _create_project(tmp)
            cart_path = os.path.join(root, "sample_cart.cart")
            icon_path = os.path.join(root, "assets", "app_icon.png")
            before = read_cart_file(cart_path, validate_files=True).project.id
            workspace = Workspace()
            workspace.set_project_root(root)

            workspace.open_file(icon_path)

            after = read_cart_file(cart_path, validate_files=True).project.id
            self.assertEqual(after, before)
            workspace.deleteLater()


def _write_png(path: str, width: int, height: int) -> None:
    image = QImage(width, height, QImage.Format_ARGB32)
    image.fill(QColor("#4fc3f7"))
    if not image.save(path, "PNG"):
        raise AssertionError(f"failed to write PNG: {path}")


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _create_project(tmp: str) -> str:
    return create_project(
        {
            "template": "cartdark_os",
            "project_name": "sample_cart",
            "location": tmp,
            "options": {"create_readme": False, "create_gitignore": False},
        }
    )


if __name__ == "__main__":
    unittest.main()
