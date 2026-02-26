from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QCheckBox, QSpinBox, QComboBox,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QGridLayout,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
import os
import re
from ..icons import get_icon
from ...state.settings_store import SettingsStore


class NewProjectDialog(QDialog):
    """新建项目对话框"""
    project_created = Signal(dict)  # 项目创建信号，传递配置信息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumSize(800, 600)

        # 存储表单数据
        self.project_name = ""
        self.location = ""
        self.template = "blank"

        # 读取上次使用的项目位置
        self._settings = SettingsStore()

        # 模板信息
        self.templates = {
            "blank": {
                "name": "空白项目",
                "description": "创建一个空的项目结构。",
                "enabled": True
            },
            "cartdark_os": {
                "name": "cartdark-os",
                "description": "创建一个 cartdark-os 项目。",
                "enabled": True
            }
        }

        self.setup_ui()
        self.connect_signals()

        # 用上次保存的路径预填位置栏
        last_location = self._settings.last_project_location
        if last_location:
            self.location_edit.setText(last_location)

        self.update_project_path()
        self.update_project_tree()
        self.validate_form()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)

        # 主分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：模板选择
        template_widget = QWidget()
        template_layout = QVBoxLayout(template_widget)

        template_group = QGroupBox("模板")
        template_group_layout = QVBoxLayout(template_group)

        self.template_list = QListWidget()
        self.template_list.setSelectionMode(QListWidget.SingleSelection)

        # 添加模板项
        for template_id, template_info in self.templates.items():
            item = QListWidgetItem(template_info["name"])
            item.setData(Qt.UserRole, template_id)

            if not template_info["enabled"]:
                item.setText(f"{template_info['name']} (即将推出)")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

            self.template_list.addItem(item)

        # 默认选择第一个模板
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

        template_group_layout.addWidget(self.template_list)
        template_layout.addWidget(template_group)

        # 模板描述
        self.template_description = QLabel(self.templates["blank"]["description"])
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("color: #888; margin-top: 10px;")
        template_layout.addWidget(self.template_description)

        splitter.addWidget(template_widget)

        # 右侧：表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        # 项目信息组
        project_group = QGroupBox("项目信息")
        project_layout = QGridLayout(project_group)

        # 项目名称
        project_layout.addWidget(QLabel("项目名称:"), 0, 0)
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("输入项目名称")
        project_layout.addWidget(self.project_name_edit, 0, 1)

        # 项目位置
        project_layout.addWidget(QLabel("位置:"), 1, 0)
        location_layout = QHBoxLayout()
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("选择项目位置")
        location_layout.addWidget(self.location_edit)

        self.browse_button = QPushButton("浏览...")
        location_layout.addWidget(self.browse_button)
        project_layout.addLayout(location_layout, 1, 1)

        # 项目路径预览
        project_layout.addWidget(QLabel("项目路径:"), 2, 0)
        self.project_path_preview = QLineEdit()
        self.project_path_preview.setReadOnly(True)
        self.project_path_preview.setStyleSheet("color: gray;")
        project_layout.addWidget(self.project_path_preview, 2, 1)

        form_layout.addWidget(project_group)

        # 显示选项组
        self.display_group = QGroupBox("显示选项")
        display_layout = QGridLayout(self.display_group)

        # 宽度
        display_layout.addWidget(QLabel("宽度:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(1)
        self.width_spin.setMaximum(4096)
        self.width_spin.setValue(800)
        display_layout.addWidget(self.width_spin, 0, 1)

        # 高度
        display_layout.addWidget(QLabel("高度:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(1)
        self.height_spin.setMaximum(4096)
        self.height_spin.setValue(480)
        display_layout.addWidget(self.height_spin, 1, 1)

        # 格式
        display_layout.addWidget(QLabel("格式:"), 2, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem("ARGB8888")
        self.format_combo.addItem("RGB888")
        self.format_combo.addItem("RGB565")
        self.format_combo.addItem("RGB555")
        display_layout.addWidget(self.format_combo, 2, 1)

        form_layout.addWidget(self.display_group)

        # 选项组
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)

        self.create_readme_check = QCheckBox("创建 README.md")
        self.create_readme_check.setChecked(True)
        options_layout.addWidget(self.create_readme_check)

        self.create_gitignore_check = QCheckBox("创建 .gitignore")
        self.create_gitignore_check.setChecked(True)
        options_layout.addWidget(self.create_gitignore_check)

        self.open_after_creation_check = QCheckBox("创建后打开项目")
        self.open_after_creation_check.setChecked(True)
        options_layout.addWidget(self.open_after_creation_check)

        form_layout.addWidget(options_group)

        # 项目树预览
        tree_group = QGroupBox("项目树预览")
        tree_layout = QVBoxLayout(tree_group)

        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setSortingEnabled(False)
        tree_layout.addWidget(self.project_tree)

        form_layout.addWidget(tree_group)

        splitter.addWidget(form_widget)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.cancel_button)

        self.create_button = QPushButton("创建")
        self.create_button.setEnabled(False)
        button_layout.addWidget(self.create_button)

        main_layout.addLayout(button_layout)

    def connect_signals(self):
        """连接信号"""
        # 模板选择
        self.template_list.currentItemChanged.connect(self.on_template_changed)

        # 表单输入
        self.project_name_edit.textChanged.connect(self.on_project_name_changed)
        self.location_edit.textChanged.connect(self.on_location_changed)
        self.browse_button.clicked.connect(self.on_browse_location)

        # 显示选项
        self.width_spin.valueChanged.connect(self.update_project_tree)
        self.height_spin.valueChanged.connect(self.update_project_tree)
        self.format_combo.currentTextChanged.connect(self.update_project_tree)

        # 选项
        self.create_readme_check.stateChanged.connect(self.update_project_tree)
        self.create_gitignore_check.stateChanged.connect(self.update_project_tree)

        # 按钮
        self.cancel_button.clicked.connect(self.reject)
        self.create_button.clicked.connect(self.on_create)

    def on_template_changed(self, current, previous):
        """模板选择变更"""
        if current:
            template_id = current.data(Qt.UserRole)
            self.template = template_id
            self.template_description.setText(self.templates[template_id]["description"])

            # 根据模板类型控制显示选项的可见性
            if template_id == "cartdark_os":
                self.display_group.hide()
            else:
                self.display_group.show()

            self.update_project_tree()

    def on_project_name_changed(self, text):
        """项目名称变更"""
        self.project_name = text
        self.update_project_path()
        self.update_project_tree()
        self.validate_form()

    def on_location_changed(self, text):
        """项目位置变更"""
        self.location = text
        self.update_project_path()
        self.validate_form()

    def on_browse_location(self):
        """浏览位置"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择项目位置", self.location or os.path.expanduser("~"
                                                                      ))
        if directory:
            self.location_edit.setText(directory)

    def update_project_path(self):
        """更新项目路径预览"""
        if self.location and self.project_name:
            project_path = os.path.join(self.location, self.project_name, f"{self.project_name}.cart")
            self.project_path_preview.setText(project_path)
        else:
            self.project_path_preview.setText("")

    def update_project_tree(self):
        """更新项目树预览"""
        # 清空树
        self.project_tree.clear()

        if not self.project_name:
            return

        # 根节点
        root_item = QTreeWidgetItem(self.project_tree, [self.project_name])

        # 收集所有顶层条目：(is_folder, name, children)
        entries = []

        # 普通文件
        entries.append((False, f"{self.project_name}.cart", []))
        entries.append((False, f"{self.project_name}.pack.json", []))

        # 选项文件
        if self.create_readme_check.isChecked():
            entries.append((False, "README.md", []))
        if self.create_gitignore_check.isChecked():
            entries.append((False, ".gitignore", []))

        # cartdark-os 模板专属文件夹
        if self.template == "cartdark_os":
            entries.append((True, "input", ["input.input_binding"]))
            entries.append((True, "main", ["Layer0.collection", "Layer1.collection"]))
            entries.append((True, "res", []))

        # 统一排序：文件夹在前，同类按 a-z（忽略大小写和前导点）
        entries.sort(key=lambda x: (not x[0], x[1].lstrip(".").lower()))

        # 添加到树
        for is_folder, name, children in entries:
            item = QTreeWidgetItem(root_item, [name])
            if is_folder:
                if name == "input":
                    # input 文件夹使用输入图标
                    item.setIcon(0, get_icon("input"))
                    for child_name in sorted(children, key=lambda n: n.lower()):
                        child_item = QTreeWidgetItem(item, [child_name])
                        # input 文件夹内的文件也使用输入图标
                        child_item.setIcon(0, get_icon("input"))
                elif name == "res":
                    # res 文件夹使用依赖图标
                    item.setIcon(0, get_icon("dependency"))
                    for child_name in sorted(children, key=lambda n: n.lower()):
                        child_item = QTreeWidgetItem(item, [child_name])
                        child_item.setIcon(0, get_icon("file"))
                else:
                    # 其他文件夹使用文件夹图标
                    item.setIcon(0, get_icon("folder"))
                    for child_name in sorted(children, key=lambda n: n.lower()):
                        child_item = QTreeWidgetItem(item, [child_name])
                        # .collection 文件使用图层图标
                        if child_name.endswith(".collection"):
                            child_item.setIcon(0, get_icon("layer"))
                        else:
                            child_item.setIcon(0, get_icon("file"))
            else:
                # 文件图标
                if name.endswith(".md"):
                    # md 文件使用代码文件图标
                    item.setIcon(0, get_icon("code"))
                elif name.endswith(".json"):
                    # json 文件使用结构体图标
                    item.setIcon(0, get_icon("struct"))
                elif name == ".gitignore":
                    # .gitignore 文件使用不使用图标
                    item.setIcon(0, get_icon("unused"))
                else:
                    # 其他文件使用文件图标
                    item.setIcon(0, get_icon("file"))

        # 展开所有节点
        self.project_tree.expandAll()

    def validate_form(self):
        """验证表单"""
        is_valid = True

        # 验证项目名称
        if not self.project_name:
            self.project_name_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        elif self.project_name.startswith("."):
            self.project_name_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        elif not re.match(r'^[A-Za-z0-9_-]+$', self.project_name):
            self.project_name_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        else:
            self.project_name_edit.setStyleSheet("")

        # 验证位置
        if not self.location:
            self.location_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        elif not os.path.exists(self.location):
            self.location_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        elif not os.path.isdir(self.location):
            self.location_edit.setStyleSheet("border: 1px solid red;")
            is_valid = False
        else:
            self.location_edit.setStyleSheet("")

        # 启用/禁用创建按钮
        self.create_button.setEnabled(is_valid)

    def on_create(self):
        """创建项目"""
        from ...project.scaffold import create_project, ScaffoldError

        config = {
            "template": self.template,
            "project_name": self.project_name,
            "location": self.location,
            "project_path": self.project_path_preview.text(),
            "display": {
                "width": self.width_spin.value(),
                "height": self.height_spin.value(),
                "format": self.format_combo.currentText()
            },
            "options": {
                "create_readme": self.create_readme_check.isChecked(),
                "create_gitignore": self.create_gitignore_check.isChecked(),
                "open_after_creation": self.open_after_creation_check.isChecked()
            }
        }

        self.create_button.setEnabled(False)

        try:
            project_root = create_project(config)
        except ScaffoldError as e:
            QMessageBox.critical(self, "创建失败", str(e))
            self.create_button.setEnabled(True)
            return
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "未知错误", traceback.format_exc())
            self.create_button.setEnabled(True)
            return

        # 保存本次选择的位置，下次打开对话框时自动填入
        self._settings.last_project_location = self.location

        config["project_root"] = project_root
        self.project_created.emit(config)
        self.accept()