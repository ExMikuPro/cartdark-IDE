from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QModelIndex, QSize


class AssetsDelegate(QStyledItemDelegate):
    """
    资源面板的自定义委托。

    功能：
    - 根节点使用加粗字体
    - 鼠标悬停行高亮（浅色背景）
    - 统一行高
    """

    ROW_HEIGHT = 24          # 每行高度（像素）
    INDENT_EXTRA = 4         # 额外缩进补偿

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = super().sizeHint(option, index)
        return QSize(size.width(), self.ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # 判断是否为顶层根节点（depth == 0 的子节点）
        is_root = not index.parent().isValid()

        if is_root:
            # 根节点加粗
            font = QFont(option.font)
            font.setBold(True)
            option = QStyleOptionViewItem(option)
            option.font = font

        super().paint(painter, option, index)