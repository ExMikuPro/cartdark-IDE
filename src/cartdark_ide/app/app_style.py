import qdarktheme

def setup_app_style():
    """设置应用样式"""
    # 使用 qdarktheme 设置深色主题
    qdarktheme.setup_theme("dark")

    # 这里可以添加自定义的 QSS 补丁
    # 例如：
    # app.setStyleSheet(qdarktheme.load_stylesheet() + custom_qss)
