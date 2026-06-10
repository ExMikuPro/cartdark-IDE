# CartDark IDE

CartDark IDE 是一个面向 CartDark 平台的轻量集成开发环境，基于 PySide6/Qt6 构建。它提供项目管理、文件编辑和 `pack.json` 清单维护等工作流，并为 CartDark OS 的 LTDC 双层渲染模型提供原生支持。

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
- 多标签页代码编辑器，支持 Lua / JSON 语法高亮，并为 CartDark 新 Lua API 与项目 JSON key 提供本地代码补全
- 代码补全支持 `Ctrl+Space` / `Alt+/` 手动触发，也会在输入 `.`, `:`, `"` 等上下文字符时弹出
- Lua 编辑支持基础关键字、常用语法片段和受限标准库补全，并提供自动缩进、Tab/Shift+Tab、成对括号/引号和括号匹配高亮
- CartDark Lua API 补全项带有简短说明，鼠标悬停在已知 API 名称上会显示本地 tooltip
- **打开于...** 菜单：可选「编辑器」（可视化）或「文本」（原始 JSON）两种模式打开同一文件
- 内嵌查找栏（`⌘F`）：实时高亮所有匹配、上/下跳转、支持大小写匹配
- 文件保存状态追踪，标签页显示修改标记（`●`）

### 可视化编辑器
| 文件类型 | 编辑器 |
|---|---|
| `.cart` | 工程设置编辑器（Project / Platforms / Bootstrap / Display 四栏导航） |
| `.layer` | 基础 2D 编辑器（节点列表 / 2D 画布 / 属性检查器，读写 `canvas` / `node` 结构） |
| `.input_binding` | 旧输入绑定编辑器（仅用于打开已有文件；新 `cartdark_os` 模板不生成） |
| `.png` / `.jpg` / `.jpeg` / `.bmp` | 图片预览编辑器（只读预览、适配窗口、100%、缩放和平移、尺寸信息） |

打开 `.cart` 项目后，IDE 会读取 `bootstrap.entry`、`bootstrap.layer0`、`bootstrap.layer1`、项目元信息、`platforms.cartdark-os.app_icon` 和 `display.width` / `display.height`，并自动进入 `bootstrap.layer1` 对应的 2D 编辑器。若该 `.layer` 文件不存在，编辑器会创建空白编辑状态但不会修改 `.cart`；保存时写入 `bootstrap.layer1` 指向的路径。新建 `.layer` 的 `canvas.width` / `canvas.height` 默认来自 `.cart.display`；读取已有 `.layer` 时，2D 编辑器必须使用 `.layer.canvas.width` / `.layer.canvas.height`。

图片预览编辑器用于查看项目内图片资源，包括默认 `assets/app_icon.png`。它不提供裁剪、绘图、滤镜、格式转换或覆盖保存能力；信息栏会显示文件名、项目相对路径、图片尺寸和当前缩放比例，便于确认 Launcher 图标是否为 `200x200`。

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
| `Ctrl+Space` / `Alt+/` | 触发代码补全 |
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

### `cartdark_os` 新建项目结构

```text
my_app/
├── my_app.cart
├── pack.json
├── scripts/
│   └── main.lua
├── layers/
│   └── default.layer
└── assets/
    └── app_icon.png
```

新建 Cart 项目时，IDE 会从内置模板资源复制默认 Launcher 应用图标到 `assets/app_icon.png`；该图标固定要求为 `200x200`，并由 `.cart` 的 `platforms.cartdark-os.app_icon` 默认指向。

### `.cart` — 工程描述文件

```json
{
  "format": "CART_PROJECT_v1.00",
  "bootstrap": {
    "entry": "scripts/main.lua",
    "layer0": "",
    "layer1": "layers/default.layer"
  },
  "project": {
    "id": "0x3FA92C10B8D4E601",
    "title": "My Cart",
    "title_zh": "我的卡带",
    "version": "0.1.0",
    "developer": "Developer Name",
    "min_fw": "0.1.0"
  },
  "platforms": {
    "cartdark-os": {
      "app_icon": "assets/app_icon.png"
    }
  },
  "display": {
    "width": 800,
    "height": 480
  }
}
```

`project.id` 由 IDE 在新建项目时生成，格式为 `0x` + 16 位十六进制。普通保存不会重新生成该 ID；`bootstrap` 和 `platforms.cartdark-os.app_icon` 中的路径均以项目根目录为基准。新建项目默认生成 `assets/app_icon.png` 作为 Launcher 应用图标，图标必须是 `200x200`，且 `.cart` 不记录图标尺寸。`display.width` 和 `display.height` 是正整数，2D 编辑器使用它们作为画布尺寸。

### `.layer` — 图层描述文件

最小合法 `.layer`：

```json
{
  "canvas": {
    "width": 800,
    "height": 480
  },
  "node": []
}
```

新建 `.layer` 时，`canvas.width` / `canvas.height` 默认来自当前 `.cart.display`。当前基础 2D 编辑器支持 `image` node，并保存 `id`、`type`、`name`、`path` 和 `position.x` / `position.y`。

### `pack.json` — XHGC_PACK v1.1 打包清单

```json
{
  "format": "XHGC_PACK",
  "pack_version": 1,
  "meta": {
    "title": "my_app",
    "entry": "scripts/main.lua",
    "cart_id": "0x0000000000000001"
  },
  "icon": {
    "path": "assets/app_icon.png",
    "format": "ARGB8888",
    "width": 200,
    "height": 200
  },
  "hash": {
    "header_crc32": true,
    "image_crc32": false,
    "per_chunk_crc32": false,
    "per_file_crc32": false
  },
  "build": {
    "alignment_bytes": 4096,
    "deterministic": true,
    "fail_on_conflict": true
  },
  "chunks": [
    { "type": "MANF", "source": "inline_meta", "name": "meta/manifest.json" },
    { "type": "LUA", "glob": "scripts/**/*.lua", "name_prefix": "", "compress": "none" },
    { "type": "RES", "glob": "layers/**/*.layer", "name_prefix": "", "compress": "none" }
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
        │   ├── input_binding_editor.py
        │   └── editor2d/             # 基础 2D layer 编辑器
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
