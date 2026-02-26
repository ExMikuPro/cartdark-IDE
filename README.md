# CartDark IDE

CartDark IDE 是一个面向 CartDark 平台的轻量集成开发环境，基于 PySide6/Qt6 构建。它提供项目管理、文件编辑、输入绑定配置等一站式工作流，并为 CartDark OS 的 LTDC 双层渲染模型提供原生支持。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)

---

## 功能一览

### 项目管理
- 新建项目（支持 `blank` / `cartdark_os` 两种模板）
- 打开 / 关闭项目，自动恢复上次打开路径
- 资源面板树形展示，支持右键菜单（新建、重命名、删除、在 Finder/资源管理器中显示）
- 文件删除时自动关闭对应标签页

### 编辑器
- 多标签页代码编辑器，支持 Lua 语法高亮
- **打开于...** 菜单：可选「编辑器」（可视化）或「文本」（原始 JSON）两种模式打开同一文件
- 内嵌查找栏（`⌘F`）：实时高亮所有匹配、上/下跳转、支持大小写匹配
- 文件保存状态追踪，标签页显示修改标记（`●`）

### 可视化编辑器
| 文件类型 | 编辑器 |
|---|---|
| `.cart` | 工程设置编辑器（Project / Display / Bootstrap 三栏导航） |
| `.input_binding` | 输入绑定编辑器（Pin / Touch / Gamepad 三张触发表） |

### 主题
- 支持**暗色 / 亮色**主题切换（菜单 → 窗口 → 主题）
- 所有自定义组件（编辑器、标签栏、可视化编辑器）全部响应主题切换，实时刷新

### 快捷键

| 快捷键 | 功能 |
|---|---|
| `⌘S` | 保存当前文件 |
| `⌘⇧S` | 全部保存 |
| `⌘W` | 关闭当前标签 |
| `⌘⇧T` | 重新打开最近关闭的文件 |
| `⌘Z` / `⌘⇧Z` | 撤销 / 重做 |
| `⌘F` | 在当前文件中查找 |
| `⌘N` | 新建项目 |
| `⌘O` | 打开项目 |
| `⌘P` | 聚焦资源面板 |
| `⌘B` | 构建并运行 |
| `F5` | 启动调试器 |
| `⌘⇧F` | 在文件中搜索 |
| `⌘1` / `⌘2` / `⌘3` | 切换面板显示 |

> Windows / Linux 上 `⌘` 对应 `Ctrl`。

---

## 项目文件格式

CartDark IDE 使用一套自定义的 JSON 格式管理工程文件。

### `.cart` — 工程描述文件

```json
{
  "format": "CART_PROJECT",
  "version": 1,
  "project": { "name": "my_app", "template": "cartdark_os", "id": "<uuid>" },
  "display": { "width": 800, "height": 480, "format": "ARGB8888" },
  "bootstrap": {
    "mode": "LTDC",
    "layers": [
      { "id": 0, "collection": "/main/Layer0.collection", "alpha": 255, "enabled": true },
      { "id": 1, "collection": "/main/Layer1.collection", "alpha": 255, "enabled": true }
    ]
  }
}
```

### `.input_binding` — 输入绑定文件

```json
{
  "format": "CART_INPUT_BINDING",
  "version": 1,
  "name": "game",
  "pin_triggers":     [{ "input": "PA0",       "action": "ok",    "event": "press" }],
  "touch_triggers":   [{ "input": "TOUCH_TAP", "action": "touch", "event": "press" }],
  "gamepad_triggers": [{ "input": "PAD_A",     "action": "jump",  "event": "press" }]
}
```

### `board/pins.json` — 板级引脚列表（由模板自动生成，无需手动维护）

```json
{
  "format": "CART_BOARD_PINS",
  "version": 1,
  "pins": [
    { "id": "PA0", "label": "PA0", "tags": ["gpio", "exti"] }
  ]
}
```

---

## 安装与运行

**依赖要求**

- Python 3.9+
- PySide6
- pyqtdarktheme (`qdarktheme`)

**安装依赖**

```bash
pip install PySide6 pyqtdarktheme
```

**运行**

```bash
python main.py
```

---

## 目录结构

```
cartdark-IDE/
├── main.py
└── src/cartdark_ide/
    ├── project/          # 工程文件读写、schema、脚手架
    ├── services/         # 项目服务、最近项目
    ├── state/            # 设置持久化 (QSettings)
    └── ui/
        ├── central/      # 工作区、编辑器、可视化编辑器
        │   ├── workspace.py
        │   ├── editor_host.py        # 代码编辑器 + 查找栏
        │   ├── cart_editor.py        # .cart 可视化编辑器
        │   └── input_binding_editor.py
        ├── docks/        # 资源面板、修改文件、大纲、属性、底部
        ├── dialogs/      # 新建/打开项目对话框
        ├── widgets/      # 自定义控件（TabHeader 等）
        ├── theme.py      # 主题颜色 token 系统
        ├── main_window.py
        ├── menus.py
        └── shortcuts.py
```

---

## 贡献

欢迎提交 Issue 和 Pull Request。

---

## 致谢

- [PySide6](https://doc.qt.io/qtforpython/) — Qt for Python 官方绑定
- [pyqtdarktheme](https://github.com/5yutan5/PyQtDarkTheme) — 暗色/亮色主题
