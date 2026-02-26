from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import QApplication
import os

# 图标缓存（区分亮/暗模式）
_icon_cache = {}

# 图标文件映射
_icon_files = {
    "folder": "文件夹.png",
    "file": "文件.png",
    "code": "代码文件.png",
    "dependency": "依赖.png",
    "settings": "设置.png",
    "input": "输入.png",
    "struct": "结构体.png",
    "unused": "不使用.png",
    "layer": "图层.png"
}

def is_dark_mode() -> bool:
    """检测是否为暗色模式"""
    from PySide6.QtGui import QPalette
    bg = QApplication.palette().color(QPalette.ColorRole.Window)
    return bg.lightness() < 128

def _invert_pixmap(pixmap: QPixmap) -> QPixmap:
    """反转 pixmap 的 RGB 颜色，保留 alpha 通道"""
    inverted = QPixmap(pixmap.size())
    inverted.fill(QColor(0, 0, 0, 0))
    for x in range(pixmap.width()):
        for y in range(pixmap.height()):
            color = pixmap.pixelColor(x, y)
            if color.alpha() > 0:
                inverted.setPixelColor(x, y, QColor(
                    255 - color.red(),
                    255 - color.green(),
                    255 - color.blue(),
                    color.alpha()
                ))
    return inverted

def get_icon(name: str) -> QIcon:
    """获取图标，暗色模式下自动反转颜色"""
    dark = is_dark_mode()
    cache_key = f"{name}_{'dark' if dark else 'light'}"

    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    icon_path = os.path.join(
        os.path.dirname(__file__),
        "resources", "icons",
        _icon_files.get(name, "文件.png")
    )

    if not os.path.exists(icon_path):
        print(f"[icons] Icon not found: {icon_path}")
        return QIcon()

    pixmap = QPixmap(icon_path)
    if dark:
        pixmap = _invert_pixmap(pixmap)

    icon = QIcon(pixmap)
    _icon_cache[cache_key] = icon
    return icon

def clear_cache():
    """清除图标缓存（切换主题时调用）"""
    _icon_cache.clear()