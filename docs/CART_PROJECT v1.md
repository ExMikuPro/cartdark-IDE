# CART 工程文件规范（.cart）v1

> 状态：稳定
>
> 目标：定义 cartdark-IDE 工程文件 `*.cart` 的 JSON 结构，用于描述工程元信息、显示目标参数、以及 STM32 LTDC 两层启动配置（Layer0/Layer1）。
>
> 关键原则：
> 1. `.cart` 只描述“工程/IDE 语义”（工程名、显示参数、启动两层入口）。
> 2. `.cart` 不承载打包清单规则；打包清单由项目根目录的 `pack.json` 负责。
> 3. 字段演进遵循“只增不破坏”，老工程文件必须可被新 IDE 打开。

---

## 1. 文件格式与约束

- 文件扩展名：`*.cart`
- 内容编码：UTF-8
- 内容格式：JSON（对象）
- 存放位置：项目根目录
- 推荐命名：`<projectName>.cart`（例：`aaa.cart`）

---

## 2. 顶层字段（Schema 总览）

顶层对象包含以下字段：

- `format`：文件类型标识（推荐）
- `version`：结构版本（必填）
- `project`：工程元信息（必填）
- `display`：显示目标（必填）
- `bootstrap`：启动配置（必填，固定两层 LTDC）

---

## 3. 字段定义（字段表）

### 3.1 顶层识别与版本

| 字段路径 | 类型 | 必填 | 约束/默认 | 说明 |
|---|---|---:|---|---|
| `format` | string | 否（推荐） | 固定 `"CART_PROJECT"` | 工具/IDE 识别标记 |
| `version` | int | 是 | 固定 `1` | `.cart` 结构版本 |

---

### 3.2 工程元信息 `project`

| 字段路径 | 类型 | 必填 | 约束/默认 | 说明 |
|---|---|---:|---|---|
| `project` | object | 是 |  | 工程元信息容器 |
| `project.name` | string | 是 |  | 工程名（IDE 展示用） |
| `project.template` | string | 是 |  | 模板标识（例：`cartdark_os`） |
| `project.id` | string | 是（推荐强制） | UUID v4 字符串 | 工程唯一 ID（用于缓存/索引/最近项目等稳定关联） |

> 建议：新建项目时 **必须生成** `project.id`（UUID v4）。

---

### 3.3 显示目标 `display`

| 字段路径 | 类型 | 必填 | 约束/默认 | 说明 |
|---|---|---:|---|---|
| `display` | object | 是 |  | 显示目标参数 |
| `display.width` | int | 是 |  | 宽（像素） |
| `display.height` | int | 是 |  | 高（像素） |
| `display.format` | string | 是 | 固定 `"ARGB8888"` | 像素格式（第一版统一） |

> 说明：本规范 v1 中 `display.format` 固定为 `ARGB8888`，以对齐你当前渲染/资源体系。

---

### 3.4 启动配置 `bootstrap`（固定两层 LTDC）

#### 总体约束

- `bootstrap.layers` **必须存在且长度固定为 2**
- `layers[0].id` 必须为 `0`（Layer0）
- `layers[1].id` 必须为 `1`（Layer1）
- v1 **不包含** `blend` 字段：默认行为为“透明叠加”（即上层带 alpha 覆盖下层）
- `alpha` 取值范围：0~255

| 字段路径 | 类型 | 必填 | 约束/默认 | 说明 |
|---|---|---:|---|---|
| `bootstrap` | object | 是 |  | LTDC 启动配置容器 |
| `bootstrap.mode` | string | 是 | 固定 `"ltdc_2layer"` | 表示固定两层模式 |
| `bootstrap.layers` | array | 是 | 长度固定 2 | 两层配置数组（Layer0/Layer1） |
| `bootstrap.layers[i].id` | int | 是 | 仅允许 0 或 1 | LTDC 层 ID |
| `bootstrap.layers[i].enabled` | bool | 是 | 默认 `true` | 层是否启用 |
| `bootstrap.layers[i].collection` | string | 是 |  | 该层默认加载的 collection 路径 |
| `bootstrap.layers[i].alpha` | int | 是 | 默认 `255` | 全局透明度（0~255） |

---

## 4. 兼容旧版 `.cart`（重要）

为兼容旧工程文件（只有 `bootstrap.main_collection` 的情况），IDE 读取时必须支持以下回退规则：

- 若存在 `bootstrap.layers`：**优先使用**
- 否则若存在 `bootstrap.main_collection`：
  - 视为 Layer0 的 `collection`
  - Layer1 使用默认值（一般 `enabled=false` 或 `collection="/main/Layer1.collection"`，由 IDE 自行决定）

> 说明：新建工程必须输出新结构（`bootstrap.layers`），旧结构仅用于兼容读取。

---

## 5. 新建项目时的 `.cart` 推荐模板（最终）

新建项目时，IDE 必须生成如下结构（示例）：

```json
{
  "format": "CART_PROJECT",
  "version": 1,

  "project": {
    "name": "aaa",
    "template": "cartdark_os",
    "id": "550e8400-e29b-41d4-a716-446655440000"
  },

  "display": {
    "width": 800,
    "height": 480,
    "format": "ARGB8888"
  },

  "bootstrap": {
    "mode": "ltdc_2layer",
    "layers": [
      {
        "id": 0,
        "enabled": true,
        "collection": "/main/Layer0.collection",
        "alpha": 255
      },
      {
        "id": 1,
        "enabled": true,
        "collection": "/main/Layer1.collection",
        "alpha": 255
      }
    ]
  }
}