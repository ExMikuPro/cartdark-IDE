from PySide6.QtGui import QIcon
import os

# 图标缓存
_icon_cache = {}

def get_icon(name):
    """获取图标"""
    if name in _icon_cache:
        return _icon_cache[name]

    # 这里可以从主题或文件路径加载图标
    # 目前返回空图标
    icon = QIcon()
    _icon_cache[name] = icon
    return icon
