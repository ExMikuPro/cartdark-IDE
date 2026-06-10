# XHGC `.cart` 项目文件格式规范

> 当前协议版本：`CART_PROJECT_v1.00`
>
> `.cart` 是 XHGC IDE / CartDark IDE 使用的 Cart 项目描述文件，采用 UTF-8 JSON 文本格式。它不是运行时二进制卡带包，也不定义 `cart.bin`、MANF、INDEX、DATA 等打包格式。

## 1. 定位

`.cart` 只描述 IDE 打开、展示和维护 Cart 项目所需的工程语义：

- 协议版本。
- 卡带启动入口。
- LTDC layer 启动文件绑定。
- Launcher 展示用基础信息。
- 平台相关配置，例如 CartDark OS 图标。
- 目标屏幕尺寸。

打包输入规则由项目根目录的 `pack.json` 描述；`.cart` 不承载 chunks、hash、alignment、compression 等打包规则。

## 2. 文件约束

| 项目 | 约束 |
|---|---|
| 扩展名 | `.cart` |
| 编码 | UTF-8 |
| 格式 | JSON |
| 根节点 | JSON Object |
| 存放位置 | 项目根目录 |
| 路径基准 | 项目根目录 |
| 当前 `format` | `CART_PROJECT_v1.00` |

## 3. 顶层结构

顶层推荐按固定顺序包含以下 5 个协议字段：

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

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `format` | string | 是 | `.cart` 协议版本 |
| `bootstrap` | object | 是 | 启动入口与 LTDC layer 绑定 |
| `project` | object | 是 | Launcher 与项目基础信息 |
| `platforms` | object | 是 | 平台相关配置 |
| `display` | object | 是 | 目标屏幕尺寸 |

## 4. 字段定义

### 4.1 `format`

`format` 是协议版本字符串。当前唯一支持值为：

```json
"CART_PROJECT_v1.00"
```

后续协议升级可使用类似 `CART_PROJECT_v1.01`、`CART_PROJECT_v2.00` 的版本号。IDE 必须对不支持的 `format` 给出明确错误。

### 4.2 `bootstrap`

`bootstrap` 描述卡带启动时需要加载的入口文件。

| 字段 | 类型 | 必填 | 默认值 | 约束 |
|---|---|---:|---|---|
| `bootstrap.entry` | string | 是 | `scripts/main.lua` | 应指向 `.lua` 文件 |
| `bootstrap.layer0` | string | 是 | `""` | 空字符串表示未绑定；非空时应指向 `.layer` 文件 |
| `bootstrap.layer1` | string | 是 | `layers/default.layer` | 应指向 `.layer` 文件 |

说明：

- `entry` 是 Lua 入口文件路径。
- `layer0` 对应 LTDC layer0，可为空。
- `layer1` 对应 LTDC layer1，新建项目默认绑定 `layers/default.layer`。

### 4.3 `project`

`project` 描述 Launcher 和项目基础信息。

| 字段 | 类型 | 必填 | 用户可改 | 说明 |
|---|---|---:|---:|---|
| `project.id` | string | 是 | 否 | IDE 管理的卡带 ID |
| `project.title` | string | 是 | 是 | Launcher 默认显示名称 |
| `project.title_zh` | string | 是 | 是 | Launcher 中文环境显示名称 |
| `project.version` | string | 是 | 是 | 应用版本号 |
| `project.developer` | string | 是 | 是 | 开发者名称 |
| `project.min_fw` | string | 是 | 是 | 运行所需最小固件版本 |

`project.id` 格式：

```regex
^0x[0-9A-Fa-f]{16}$
```

示例：

```json
"id": "0x3FA92C10B8D4E601"
```

ID 管理规则：

- 新建项目时由 IDE 自动生成随机 64-bit 十六进制 ID。
- 普通保存不得重新生成。
- 用户修改标题、版本、开发者、入口文件、layer 或图标路径时，不得影响该 ID。
- 只有“克隆项目”“另存为新卡带”等明确创建新卡带身份的操作才允许生成新 ID。

### 4.4 `platforms.cartdark-os`

当前必须支持 `cartdark-os` 平台块。

| 字段 | 类型 | 必填 | 用户可改 | 说明 |
|---|---|---:|---:|---|
| `platforms.cartdark-os.app_icon` | string | 是 | 是 | Launcher 显示图标路径 |

`app_icon` 规则：

- 路径基准为项目根目录。
- 图标文件必须存在。
- 图标尺寸必须是 `200x200`。
- 尺寸要求由协议规定，不写入 `.cart` 文件。
- 新建 Cart 项目时，IDE 默认生成 `assets/app_icon.png` 作为 Launcher 应用图标，并将 `platforms.cartdark-os.app_icon` 写为 `assets/app_icon.png`。

### 4.5 `display`

| 字段 | 类型 | 必填 | 用户可改 | 说明 |
|---|---|---:|---:|---|
| `display.width` | integer | 是 | 是 | 目标屏幕宽度，单位像素，必须为正整数 |
| `display.height` | integer | 是 | 是 | 目标屏幕高度，单位像素，必须为正整数 |

新建 `.layer` 文件时，`canvas.width` / `canvas.height` 默认来自 `.cart.display.width` / `.cart.display.height`。2D 编辑器读取已有 `.layer` 时，必须使用 `.layer.canvas.width` 和 `.layer.canvas.height`；缺失 `canvas.width` 或 `canvas.height` 应直接报错。

## 5. 路径规则

以下字段均为项目内相对路径：

```text
bootstrap.entry
bootstrap.layer0
bootstrap.layer1
platforms.cartdark-os.app_icon
```

规则：

- 使用 `/` 作为路径分隔符。
- 不使用绝对路径。
- 不使用 `..` 逃逸项目根目录。
- `bootstrap.layer0` 是唯一允许为空字符串的路径字段。

## 6. 用户可编辑规则

除 `project.id` 外，其他协议字段均允许由用户修改并保存。

实际 UI 可以选择不直接暴露 `format` 编辑；如果用户通过文本方式把 `format` 改成 IDE 不支持的协议版本，IDE 打开时必须拒绝并说明当前支持版本。

## 7. 读写规则

### 读取

IDE 读取 `.cart` 时必须：

1. 按 UTF-8 文本读取。
2. 按 JSON 解析。
3. 校验根节点和所有必填字段。
4. 校验协议版本。
5. 校验路径、扩展名、图标文件存在性和图标尺寸。
6. 失败时给出明确错误，不应静默降级为默认项目。

### 保存

IDE 保存 `.cart` 时必须：

- 写回 JSON 文本，不得写成二进制格式。
- 保留已有 `project.id`。
- 允许保存用户修改的非 ID 字段。
- 保存前执行基础校验，避免写出明显无效的路径、扩展名或图标尺寸。

## 8. 校验清单

IDE 打开或校验 `.cart` 文件时，应检查：

1. 文件存在且可读取。
2. 文件内容是合法 JSON。
3. 根节点是 JSON Object。
4. `format` 存在、类型为 string、值为支持的协议版本。
5. `bootstrap` 存在且为 object。
6. `bootstrap.entry` 存在、类型为 string、后缀为 `.lua`。
7. `bootstrap.layer0` 存在、类型为 string；为空时通过，非空时后缀为 `.layer`。
8. `bootstrap.layer1` 存在、类型为 string、后缀为 `.layer`。
9. `project` 存在且为 object。
10. `project.id` 存在、类型为 string、符合 `^0x[0-9A-Fa-f]{16}$`。
11. `project.title` 存在且为 string。
12. `project.title_zh` 存在且为 string。
13. `project.version` 存在且为 string。
14. `project.developer` 存在且为 string。
15. `project.min_fw` 存在且为 string。
16. `platforms` 存在且为 object。
17. `platforms.cartdark-os` 存在且为 object。
18. `platforms.cartdark-os.app_icon` 存在、类型为 string、文件存在、图标尺寸为 `200x200`。
19. `display` 存在且为 object。
20. `display.width` 存在、类型为 integer，且为正整数。
21. `display.height` 存在、类型为 integer，且为正整数。

常见错误应明确指出字段和原因，例如：

- `format 不支持：CART_PROJECT_v9.99；当前支持：CART_PROJECT_v1.00`
- `bootstrap.entry 必须指向 .lua 文件：scripts/main.txt`
- `platforms.cartdark-os.app_icon 图标尺寸必须为 200x200，当前为 128x128：assets/app_icon.png`

## 9. 新建项目默认输出

新建项目时 IDE 必须生成默认 `.cart`，同时创建默认入口文件、默认 layer 文件和默认图标文件。默认图标来自 IDE 内置模板资源，复制到 `assets/app_icon.png` 后作为 Launcher 应用图标使用。

默认文件：

```text
scripts/main.lua
layers/default.layer
assets/app_icon.png
```

默认 `.cart`：

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

示例中的 `project.id` 只是格式示例。实际新建项目时不得使用固定值，必须生成新的随机 ID。

默认 `layers/default.layer`：

```json
{
  "canvas": {
    "width": 800,
    "height": 480
  },
  "node": []
}
```

## 10. 非目标

本规范不定义以下内容：

- `pack.json` 的 `chunks`、`hash`、`build`、`icon.format` 等打包规则。
- `cart.bin` 的二进制布局。
- MANF、INDEX、DATA 等运行时包内结构。
- Lua 生命周期回调的调用顺序。
- `.layer` 中 `image` node 以外的复杂 2D 功能。

这些内容属于打包器、运行时或其他独立规范。
