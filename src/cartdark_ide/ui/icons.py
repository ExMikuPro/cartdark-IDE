from PySide6.QtGui import QIcon
import os

# 图标缓存
_icon_cache = {}

# 图标文件映射
_icon_files = {
    "folder": "文件夹.png",
    "file": "文件.png",
    "code": "代码文件.png",
    "dependency": "依赖.png",
    "settings": "设置.png",
    "input": "输入.png"
}

def get_icon(name):
    """获取图标"""
    if name in _icon_cache:
        return _icon_cache[name]

    # 从资源文件加载图标
    icon_path = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "icons",
        _icon_files.get(name, "文件.png")
    )
    
    icon = QIcon(icon_path)
    _icon_cache[name] = icon
    return icon