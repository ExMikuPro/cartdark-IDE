from .actions import create_actions


def create_menu_bar(window):
    """创建菜单栏"""
    menu_bar = window.menuBar()

    # 创建菜单
    file_menu = menu_bar.addMenu("文件")
    edit_menu = menu_bar.addMenu("编辑")
    view_menu = menu_bar.addMenu("视图")
    window_menu = menu_bar.addMenu("窗口")
    build_menu = menu_bar.addMenu("构建")
    debug_menu = menu_bar.addMenu("调试")
    help_menu = menu_bar.addMenu("帮助")

    # 创建操作
    actions = create_actions(window)

    # 文件菜单
    file_menu.addAction(actions["new"])
    new_project_action = actions["new_project"]
    new_project_action.triggered.connect(window.open_new_project_dialog)
    file_menu.addAction(new_project_action)
    open_action = actions["open"]
    open_action.triggered.connect(window.open_open_project_dialog)
    file_menu.addAction(open_action)
    file_menu.addAction(actions["save"])
    file_menu.addSeparator()
    file_menu.addAction(actions["exit"])

    # 编辑菜单
    edit_menu.addAction(actions["undo"])
    edit_menu.addAction(actions["redo"])
    edit_menu.addSeparator()
    edit_menu.addAction(actions["cut"])
    edit_menu.addAction(actions["copy"])
    edit_menu.addAction(actions["paste"])

    # 构建菜单
    build_menu.addAction(actions["build"])
    build_menu.addAction(actions["run"])

    # 窗口菜单
    # 添加窗口管理相关操作
    reset_layout_action = window_menu.addAction("重置布局")

    # 创建主题子菜单
    theme_submenu = window_menu.addMenu("主题")

    # 创建视图子菜单
    view_submenu = window_menu.addMenu("视图")

    # 在视图子菜单中添加带复选标记的动作
    assets_action = view_submenu.addAction("资源面板")
    assets_action.setCheckable(True)
    assets_action.setChecked(True)  # 默认显示

    changed_files_action = view_submenu.addAction("修改的文件面板")
    changed_files_action.setCheckable(True)
    changed_files_action.setChecked(True)  # 默认显示

    outline_action = view_submenu.addAction("大纲面板")
    outline_action.setCheckable(True)
    outline_action.setChecked(True)  # 默认显示

    properties_action = view_submenu.addAction("属性面板")
    properties_action.setCheckable(True)
    properties_action.setChecked(True)  # 默认显示

    bottom_action = view_submenu.addAction("底部面板")
    bottom_action.setCheckable(True)
    bottom_action.setChecked(True)  # 默认显示

    window_menu.addSeparator()
    fullscreen_action = window_menu.addAction("全屏模式")
    fullscreen_action.setCheckable(True)
    fullscreen_action.setChecked(False)  # 默认非全屏

    # 绑定事件处理
    def toggle_assets_panel():
        if hasattr(window, 'assets_dock'):
            window.assets_dock.setVisible(assets_action.isChecked())

    def toggle_changed_files_panel():
        if hasattr(window, 'changed_files_dock'):
            window.changed_files_dock.setVisible(changed_files_action.isChecked())

    def toggle_outline_panel():
        if hasattr(window, 'outline_dock'):
            window.outline_dock.setVisible(outline_action.isChecked())

    def toggle_properties_panel():
        if hasattr(window, 'properties_dock'):
            window.properties_dock.setVisible(properties_action.isChecked())

    def toggle_bottom_panel():
        if hasattr(window, 'bottom_dock'):
            window.bottom_dock.setVisible(bottom_action.isChecked())

    def toggle_fullscreen():
        if fullscreen_action.isChecked():
            window.showFullScreen()
        else:
            window.showNormal()

    def reset_layout():
        # 重置布局为默认状态
        if hasattr(window, 'assets_dock'):
            window.assets_dock.setVisible(True)
            assets_action.setChecked(True)
        if hasattr(window, 'changed_files_dock'):
            window.changed_files_dock.setVisible(True)
            changed_files_action.setChecked(True)
        if hasattr(window, 'outline_dock'):
            window.outline_dock.setVisible(True)
            outline_action.setChecked(True)
        if hasattr(window, 'properties_dock'):
            window.properties_dock.setVisible(True)
            properties_action.setChecked(True)
        if hasattr(window, 'bottom_dock'):
            window.bottom_dock.setVisible(True)
            bottom_action.setChecked(True)

        # 重置窗口大小
        window.resize(1440, 900)

        # 退出全屏模式
        if fullscreen_action.isChecked():
            fullscreen_action.setChecked(False)
            window.showNormal()

    # 主题选项
    dark_theme_action = theme_submenu.addAction("黑色")
    dark_theme_action.setCheckable(True)
    dark_theme_action.setChecked(True)  # 默认黑色主题

    light_theme_action = theme_submenu.addAction("白色")
    light_theme_action.setCheckable(True)
    light_theme_action.setChecked(False)

    # 主题切换功能
    def switch_to_dark_theme():
        if dark_theme_action.isChecked():
            import qdarktheme
            from PySide6.QtWidgets import QApplication
            qdarktheme.setup_theme("dark")

            light_theme_action.setChecked(False)
            # 更新底部面板主题
            if hasattr(window, 'bottom_dock'):
                window.bottom_dock._apply(True)
            # 强制刷新应用所有控件
            app = QApplication.instance()
            if app:
                app.processEvents()
                for widget in app.allWidgets():
                    widget.update()
                    widget.repaint()

    def switch_to_light_theme():
        if light_theme_action.isChecked():
            import qdarktheme
            from PySide6.QtWidgets import QApplication
            qdarktheme.setup_theme("light")
            dark_theme_action.setChecked(False)
            # 更新底部面板主题
            if hasattr(window, 'bottom_dock'):
                window.bottom_dock._apply(False)
            # 强制刷新应用所有控件
            app = QApplication.instance()
            if app:
                app.processEvents()
                for widget in app.allWidgets():
                    widget.update()
                    widget.repaint()

    # 连接信号
    assets_action.triggered.connect(toggle_assets_panel)
    changed_files_action.triggered.connect(toggle_changed_files_panel)
    outline_action.triggered.connect(toggle_outline_panel)
    properties_action.triggered.connect(toggle_properties_panel)
    bottom_action.triggered.connect(toggle_bottom_panel)
    fullscreen_action.triggered.connect(toggle_fullscreen)
    reset_layout_action.triggered.connect(reset_layout)
    # 连接信号
    assets_action.triggered.connect(toggle_assets_panel)
    changed_files_action.triggered.connect(toggle_changed_files_panel)
    outline_action.triggered.connect(toggle_outline_panel)
    properties_action.triggered.connect(toggle_properties_panel)
    bottom_action.triggered.connect(toggle_bottom_panel)
    reset_layout_action.triggered.connect(reset_layout)
    fullscreen_action.triggered.connect(toggle_fullscreen)
    dark_theme_action.triggered.connect(switch_to_dark_theme)
    light_theme_action.triggered.connect(switch_to_light_theme)

    return menu_bar