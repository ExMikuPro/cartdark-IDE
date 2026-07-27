# CartDark Studio

CartDark Studio 是面向 `cartdesk-os`、`xhgc-pack` 与 `cart.bin` 工作流的桌面 IDE。
项目保留 Defold Editor 成熟的原生代码编辑器与桌面布局基础，但拥有独立的
CartDark 启动链、项目模型、构建流程、产品名称和配置目录。它不要求
`game.project`，也不会从 CartDark 入口启动 Bob、Defold Engine、Target
Discovery、热重载或场景编辑系统。

本仓库仍为 `ExMikuPro/cartdark-IDE`。旧 PySide6 实现只保留在 Git 历史中，
不再作为主线源码或入口存在。

## 当前功能

- Java/JavaFX 桌面启动层和 Clojure/cljfx 工作区。
- 普通文件系统项目树，以及新建 Lua、建目录、重命名、删除、刷新和路径复制。
- 以 `pack.json` 为项目入口，校验 UTF-8 JSON 与顶层 `format: XHGC_PACK`。
- 多标签原生 Defold Canvas 代码编辑器，支持 Lua、JSON、Markdown、文本、
  C/C++ 头文件、Python 与 CMake 文本。
- 单实例文件标签、Dirty 标记、保存、全部保存、关闭确认、关闭其他、关闭右侧
  和恢复最近关闭标签。
- CartDark Lua 生命周期/API 元数据，以及不可用 Lua 标准模块的警告接口。
- 后台执行 `xhgc-pack`，流式收集 stdout/stderr、解析逐行 JSON 错误、支持取消、
  Rebuild 和生成 `build/cart.bin`。
- 构建成功后可启动 `cartdesk-simulator`；模拟器不存在不会使构建失败。
- CartDark 独立的最近项目、窗口、分栏、标签页、编辑器和工具路径设置。

## 技术栈

- Java 25
- JavaFX
- Clojure、Leiningen 与 cljfx
- Dynamo Graph
- Defold 原生代码编辑器

CartDark Studio 本身没有 Python、PySide6、PyQt、qdarktheme、Tauri、Electron、
Monaco、QPlainTextEdit 或 WebView 编辑器依赖。若所配置的当前 `xhgc-pack`
仍以 `main.py` 发布，Studio 会将它作为外部构建工具调用；这不属于 Studio
桌面运行时。

## 上游与首次初始化

当前基线来自 Defold `dev`：

```text
39c1b854e2678417b682fefc8affcfd0245cb017
```

首次构建应遵循该提交的 `editor/README.md`。Editor-only 初始化不要求本地编译
Defold Engine，可使用预构建工件：

```bash
python3 scripts/build.py shell
./scripts/build.py install_ext
cd editor
lein init 39c1b854e2678417b682fefc8affcfd0245cb017
```

需要 JDK 25、Leiningen，以及 Defold 上游初始化脚本列出的平台依赖。上面的
Python 仅用于保留的上游依赖准备脚本；完成初始化后，CartDark Studio 的编译
和启动由 JVM/Leiningen 完成。

## 构建、测试与启动

Linux 和 macOS：

```bash
./scripts/run-cartdark
./scripts/run-cartdark /absolute/path/to/project/pack.json
./scripts/run-cartdark --test
```

Windows PowerShell：

```powershell
cd editor
lein test-cartdark
lein run-cartdark
```

也可以直接传入项目目录或 `pack.json`：

```bash
cd editor
lein run-cartdark /absolute/path/to/project
lein run-cartdark /absolute/path/to/project/pack.json
```

仓库启动脚本不会引用系统 `/tmp/cartdark-*`。它依次使用：

1. `CARTDARK_JAVA_HOME` 与 `CARTDARK_LEIN`。
2. 系统 `JAVA_HOME` 和 `PATH` 中的 Leiningen。
3. `~/.local/share/cartdark-studio/toolchains/` 中的持久工具链。

Defold Editor 的预构建依赖默认位于持久目录
`~/.local/share/cartdark-studio/dynamo-home/`；也可通过
`CARTDARK_DYNAMO_HOME` 指向其他目录。启动流程不依赖仓库或系统临时目录。

IntelliJ IDEA 会自动发现 `.run/CartDark Studio.run.xml`。打开仓库后，在顶部
运行配置中选择 **CartDark Studio** 并点击运行即可，不需要为运行配置填写
任何 `/tmp` 路径。Shell Script 插件必须处于启用状态。

## 项目与构建工具

项目根目录必须包含 UTF-8 编码的 `pack.json`，且顶层字段为：

```json
{
  "format": "XHGC_PACK",
  "meta": {
    "title": "My Cart",
    "entry": "app/main.lua"
  }
}
```

可从 File 菜单选择目录或直接选择 `pack.json`。`xhgc-pack` 按以下顺序查找：

1. Settings 中保存的路径。
2. `XHGC_PACK` 环境变量。
3. `PATH` 中的 `xhgc-pack`。
4. `tools/xhgc-pack/`。
5. IDE 同级的 `../xhgc-pack/`。

快捷键为 `Ctrl/Cmd+B` 构建、`Ctrl/Cmd+Shift+B` 重建，以及
`Ctrl/Cmd+R` 构建并运行。当前真实 CLI 若为
`python main.py pack.json build/cart.bin`，适配器会按该接口调用。

模拟器路径可在 Settings 中配置，也可通过 `CARTDESK_SIMULATOR` 或 `PATH`
提供；还会检查 `tools/cartdesk-simulator/` 与 `../cartdesk-simulator/`。
Build and Run 会先保存全部文件、构建 `cart.bin`，再将输出路径作为模拟器参数。

## 配置位置

- Linux：`~/.config/cartdark-studio/`
- macOS：`~/Library/Application Support/CartDark Studio/`
- Windows：`%APPDATA%/CartDark Studio/`

## 许可证与归属

CartDark Studio 基于 Defold Editor 源码修改。Defold 原许可证、版权头、
`NOTICE`、`TOOLS_LICENSES.md` 与第三方许可材料均保留；CartDark 的附加说明见
`NOTICE_CARTDARK`，精确上游记录见 `docs/upstream/DEFOLD_COMMIT`。

Defold 及其商标归原权利人所有。CartDark Studio 由 ExMikuPro 修改，是独立产品，
不是 Defold 官方产品，也未使用 Defold Logo 作为应用 Logo。
