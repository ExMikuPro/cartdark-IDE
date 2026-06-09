# CartDark IDE Agent Guide

本文件约束在 `cartdark-IDE` 仓库内工作的自动化代理与协作者。目标是让改动贴合本仓库的实际形态：一个基于 PySide6/Qt6 的 CartDark 工程 IDE，并通过 `pack.json` 与相邻的 `xhgc-pack` 打包器、STM32 运行时生态衔接。

## Repository Scope

- 当前仓库是 IDE，不是打包器，也不是 STM32 固件工程。
- 默认只修改本仓库文件。只有用户明确要求时，才修改相邻仓库，例如 `/Volumes/Sector0/AppData/PyCharm/xhgc-pack`。
- 不要把 `xhgc-pack` 或 STM32 固件中的未确认能力写成本仓库已实现能力。
- 若 IDE、打包器文档、打包器实现之间存在差异，必须在说明或文档中标为“文档与实现差异”。

## Project Facts

- 入口：`main.py`
- 主窗口：`src/cartdark_ide/ui/main_window.py`
- 项目格式：`.cart`，实现集中在 `src/cartdark_ide/project/`
- 打包清单：`pack.json`，IDE 生成/校验/维护，打包器读取
- 输入绑定：`input/input.input_binding`
- 板级引脚表：`board/pins.json`
- 主要 UI 技术：PySide6/Qt6、`pyqtdarktheme`
- 主要模板：`blank`、`cartdark_os`

## Architecture Boundaries

- `.cart` 描述 IDE/工程语义：工程名、显示参数、LTDC 双层 bootstrap。
- `pack.json` 描述打包器输入规则：`meta`、`icon`、`hash`、`build`、`chunks`。
- `cart.bin` 格式、MANF、INDEX、DATA 的二进制布局属于打包器和运行时契约；在本仓库中只能引用或集成，不要擅自扩展格式。
- `cartdark_os` 的 LTDC collection bootstrap 与 Lua ENTRY 是不同层面的概念；修改相关模板时必须同时检查 `.cart`、`pack.json`、README 和 docs 是否一致。

## Code Exploration Policy

在做项目级探索、架构分析或跨文件改动前，优先使用 CodeGraph。

推荐顺序：

1. `codegraph_status`
2. `codegraph_explore` 理解模块或工作流
3. `codegraph_search` 定位符号
4. `codegraph_callers` / `codegraph_callees` 查看调用链
5. `codegraph_impact` 评估重构影响
6. 只读取必须修改的具体文件

如果 CodeGraph 不可用，再使用 `rg` / `rg --files`。不要在不需要时进行全仓库无差别扫描。

## Implementation Rules

- 优先遵循现有 PySide6 代码风格和本地组件结构。
- 修改 UI 行为时，检查菜单、快捷键、README 功能表是否同步。
- 修改项目模板时，检查 `src/cartdark_ide/project/scaffold.py`、`schema.py`、`pack_sync.py`、README 和 `docs/`。
- 修改文件格式时，保持“只增不破坏”；旧项目读取兼容优先。
- 不要新增大型抽象，除非它能明确减少重复或稳定 IDE 与打包器的接口。
- 避免生成或提交缓存文件，例如 `__pycache__/`、`.DS_Store`。
- 不要改动用户已有未提交内容，除非用户明确要求或该改动与当前任务直接相关。

## Documentation Update Policy

当新增、修改或删除用户可见/开发者可见行为时，必须同步更新相关 Markdown 文档。

需要更新文档的场景包括：

- 菜单、快捷键、编辑器行为或项目工作流变化
- `.cart`、`.input_binding`、`board/pins.json`、`pack.json` 字段变化
- 新增构建命令、打包器集成、输出路径或生命周期钩子
- 模板生成的目录、文件或默认内容变化
- IDE 与 `xhgc-pack` 或 STM32 运行时的接口约定变化

若无需更新文档，在最终说明中明确说明原因。

## Architecture Documentation Policy

当用户要求分析、梳理或记录架构时，创建或更新 Markdown 文档，不生成 PNG、SVG、draw.io、Excalidraw 等二进制图。

推荐内容：

- 使用 Mermaid `flowchart` 表达高层架构
- 使用 Mermaid `sequenceDiagram` 表达加载、构建、运行时顺序
- 高层图控制在 15 个节点以内
- 用实线表示源码确认关系
- 用虚线表示推测或未确认关系
- 将不确定内容标为 `推测` 或 `未确认`
- 引用真实仓库路径作为依据

相关章节可包括：

- System overview
- High-level architecture diagram
- Core module table
- Main data flow
- Project open / close flow
- Template generation flow
- Pack / build flow
- Input binding flow
- Documented facts
- Inferred relationships
- Open questions
- Referenced files
- Check results

## Cart / BIN / Packer Analysis

分析或修改打包链路时必须同时检查：

- IDE 生成侧：`src/cartdark_ide/project/schema.py`
- IDE 模板侧：`src/cartdark_ide/project/scaffold.py`
- IDE 同步侧：`src/cartdark_ide/project/pack_sync.py`
- 本仓库文档：`README.md`、`docs/CART_PROJECT v1.md`、`docs/spec-input-binding-v1.md`
- 相邻打包器仓库的实现和文档（只读，除非用户要求修改）：`xhgc-pack`

注意：

- 只确认源码或文档中真实存在的 magic、version、header、manifest、index、resource table、entry、checksum、compression、alignment 字段。
- 文档存在但实现未确认时，标为 `文档定义，源码未确认`。
- 实现和文档不一致时，增加 `文档与实现差异`。
- 不要因为常见格式有某字段，就假设 CartDark/XHGC 也有。

## Lua / Runtime Analysis

分析 Lua 生命周期时，不要假设 Defold 风格回调已经存在。只有源码确认后才能写为已实现。

需要核查的回调包括：

```lua
function init(self)
end

function final(self)
end

function fixed_update(self, dt)
end

function update(self, dt)
end

function late_update(self, dt)
end

function on_message(self, message_id, message, sender)
end

function on_input(self, action_id, action)
end

function on_reload(self)
end
```

如果只在文档或模板示例中出现，标为 `文档出现，源码未确认`。如果调用顺序无法从源码确认，标为 `顺序未确认`。

## Validation

优先使用仓库内虚拟环境：

```bash
./.venv/bin/python -m compileall -q main.py src
```

如果虚拟环境不可用，使用：

```bash
python3 -m compileall -q main.py src
```

PySide6 主窗口烟测：

```bash
QT_QPA_PLATFORM=offscreen ./.venv/bin/python -c "from PySide6.QtWidgets import QApplication; from src.cartdark_ide.ui.main_window import MainWindow; app=QApplication([]); w=MainWindow(); print(w.windowTitle())"
```

运行检查后清理新生成的 `__pycache__/`，不要把缓存留在工作区。

## Git Commit Message Style

生成提交信息前：

1. 查看 staged diff：`git diff --cached`
2. 判断单一主目的
3. 选择合适 Conventional Commit 类型
4. 写一个简短、工程化的 subject
5. 若 staged changes 无关，建议拆分提交

提交 subject 规则：

- 使用 Conventional Commit 前缀
- 常用类型：`feat:`、`fix:`、`refactor:`、`docs:`、`chore:`、`build:`、`perf:`、`style:`、`test:`
- 前缀后写简洁中文描述，必要时点出模块
- 不写冗长 subject
- 除非用户要求，不写 body
- 不提 AI、ChatGPT、Codex 或 assistant

示例：

- `feat: 接入 pack.json 构建入口`
- `fix: 修复标签关闭状态同步`
- `refactor: 调整项目模板生成逻辑`
- `docs: 更新 CartDark 生态架构说明`

除非另有要求，输出提交信息时只输出最终 subject。
