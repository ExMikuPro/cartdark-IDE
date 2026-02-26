# 输入绑定与板级引脚列表规范（v1）

> 适用：cartdark-IDE 工程  
> 模式：Defold 风格的 Input Bindings（表格：Input → Action）  
> v1 输入源：**触摸 + 引脚(GPIO) + 手柄按键（不含摇杆）**  
> 关键要求：**引脚输入只能从下拉列表选择，不能手动输入**。  
> 板级引脚列表由**项目模板自动提供**，用户不需要关心/维护。

---

## 0. 文件与职责一览

| 文件                    | 位置 | 由谁提供 | 用户是否需要关心 | 职责 |
|-----------------------|---|---|---:|---|
| `input.input_binding` | `input/` | IDE/用户编辑 | ✅需要（通过 UI 编辑） | 输入绑定：把“触摸/引脚/手柄按键”映射为动作 action |
| `pins.json`           | `board/` | **项目模板** | ❌不需要 | 引脚下拉列表数据源（合法引脚集合） |

> 说明：用户只编辑 `input.input_binding`。`board/pins.json` 属于模板资产，IDE 只读使用，不向用户暴露编辑入口。

---

## 1. `input/input.input_binding` 规范

### 1.1 文件约束
- 路径：`input/input.input_binding`
- 编码：UTF-8
- 格式：JSON
- 顶层必须为对象

### 1.2 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `format` | string | ✅ | 固定 `"CART_INPUT_BINDING"` |
| `version` | int | ✅ | 固定 `1` |
| `name` | string | ⭕ | 配置名称（IDE 显示用） |
| `pin_triggers` | array | ✅ | 引脚触发映射（input 只能从下拉列表选） |
| `touch_triggers` | array | ✅ | 触摸触发映射 |
| `gamepad_triggers` | array | ✅ | 手柄按键触发映射（不含摇杆） |

> v1 建议三个数组字段都存在（允许为空），便于 IDE 表格直接绑定。

---

### 1.3 Trigger 条目结构（统一）

`pin_triggers / touch_triggers / gamepad_triggers` 数组元素结构一致：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `input` | string | ✅ | 输入名（由所属 triggers 决定含义） |
| `action` | string | ✅ | 动作名（传入 Lua 的 action，例如 `"ok"`） |
| `event` | string | ✅ | v1 允许：`press` / `release`（最少实现 press） |

---

### 1.4 输入名约定

#### 1.4.1 Pin Triggers（引脚输入）
- `pin_triggers[].input` **必须**为 `board/pins.json` 中 `pins[].id` 的一个值
- UI 表格中必须使用 **下拉框（ComboBox）**，并设置 **不可编辑**（不可手动输入）

#### 1.4.2 Touch Triggers（触摸）
v1 推荐的输入名：
- `TOUCH_TAP`（点按）
- `TOUCH_DOWN`（按下）
- `TOUCH_UP`（抬起）

> 只需要点按时，只配置 `TOUCH_TAP` 即可。

#### 1.4.3 Gamepad Triggers（手柄按键，不含摇杆）
v1 推荐输入名：
- `PAD_A`, `PAD_B`, `PAD_X`, `PAD_Y`
- `PAD_L1`, `PAD_R1`
- `PAD_START`, `PAD_SELECT`
- `PAD_UP`, `PAD_DOWN`, `PAD_LEFT`, `PAD_RIGHT`

> v1 明确不允许出现摇杆轴类输入，如 `PAD_LX/PAD_LY/PAD_RX/PAD_RY`。

---

## 2. `board/pins.json` 规范（引脚下拉列表数据源）

### 2.1 文件约束
- 路径：`board/pins.json`
- 编码：UTF-8
- 格式：JSON
- **由项目模板提供**，用户无需编辑；IDE 默认只读使用。

### 2.2 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `format` | string | ✅ | 固定 `"CART_BOARD_PINS"` |
| `version` | int | ✅ | 固定 `1` |
| `name` | string | ⭕ | 板级/MCU 名称（显示用） |
| `pins` | array | ✅ | 引脚列表（下拉选项来源） |

### 2.3 pins 条目结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | ✅ | 引脚唯一标识（例如 `"PA0"`），也是 input_binding 里 pin input 的合法值 |
| `label` | string | ✅ | 展示文本（一般等于 id） |
| `tags` | array[string] | ⭕ | 标签（用于 IDE 筛选：如 `gpio`/`exti`/`wkup` 等） |

### 2.4 示例：`board/pins.json`

```json
{
  "format": "CART_BOARD_PINS",
  "version": 1,
  "name": "Board Template Pins",
  "pins": [
    { "id": "PA0", "label": "PA0", "tags": ["gpio", "exti"] },
    { "id": "PA1", "label": "PA1", "tags": ["gpio"] },
    { "id": "PB12", "label": "PB12", "tags": ["gpio"] },
    { "id": "PC13", "label": "PC13", "tags": ["gpio", "wkup"] }
  ]
}