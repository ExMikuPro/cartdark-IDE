# CART 工程文件规范（.cart）v1.00

> 状态：稳定
>
> 目标：定义 XHGC IDE / CartDark IDE 使用的 Cart 项目描述文件。`.cart` 是 UTF-8 JSON 文本文件，不是二进制卡带包。

## 1. 文件格式

- 文件扩展名：`*.cart`
- 内容格式：JSON Object
- 协议版本：`CART_PROJECT_v1.00`
- 存放位置：项目根目录
- 路径基准：项目根目录

## 2. 顶层结构

`.cart` 顶层推荐按固定顺序包含 5 个字段：

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

## 3. 字段定义

### `format`

`format` 是 `.cart` 文件协议版本字符串。当前固定为：

```json
"CART_PROJECT_v1.00"
```

IDE 打开项目时必须拒绝不支持的版本，并给出明确错误。

### `bootstrap`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `bootstrap.entry` | string | 是 | 卡带入口 Lua 文件路径，应指向 `.lua` 文件 |
| `bootstrap.layer0` | string | 是 | LTDC layer0 对应 `.layer` 文件路径；空字符串表示未绑定 |
| `bootstrap.layer1` | string | 是 | LTDC layer1 对应 `.layer` 文件路径，必须指向 `.layer` 文件 |

新建项目默认创建：

```text
scripts/main.lua
layers/default.layer
```

默认 bootstrap：

```json
{
  "entry": "scripts/main.lua",
  "layer0": "",
  "layer1": "layers/default.layer"
}
```

### `project`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `project.id` | string | 是 | IDE 管理的卡带 ID，格式为 `0x` + 16 位十六进制 |
| `project.title` | string | 是 | Launcher 默认显示的应用名称 |
| `project.title_zh` | string | 是 | Launcher 中文环境显示的应用名称 |
| `project.version` | string | 是 | 应用版本号 |
| `project.developer` | string | 是 | 开发者名称 |
| `project.min_fw` | string | 是 | 运行该卡带所需的最小固件版本 |

`project.id` 正则规则：

```regex
^0x[0-9A-Fa-f]{16}$
```

`project.id` 必须由 IDE 在新建项目时自动生成。普通保存不得重新生成；只有“克隆项目”“另存为新卡带”等明确操作才能生成新 ID。

### `platforms.cartdark-os`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `platforms.cartdark-os.app_icon` | string | 是 | Launcher 图标路径 |

`app_icon` 指向的图标文件必须存在于项目根目录下，尺寸固定为 `200x200`。尺寸要求由协议规定，不写入 `.cart` 文件。
新建 Cart 项目时，IDE 默认生成 `assets/app_icon.png` 作为 Launcher 应用图标，并将 `platforms.cartdark-os.app_icon` 写为 `assets/app_icon.png`。

### `display`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `display.width` | integer | 是 | 目标屏幕宽度，单位像素，必须为正整数 |
| `display.height` | integer | 是 | 目标屏幕高度，单位像素，必须为正整数 |

新建 `.layer` 文件时，`canvas.width` / `canvas.height` 默认来自 `.cart.display.width` / `.cart.display.height`。2D 编辑器读取已有 `.layer` 时，必须读取 `.layer.canvas.width` 和 `.layer.canvas.height`；缺失 `canvas.width` 或 `canvas.height` 应直接报错。

## 4. 用户可编辑规则

除 `project.id` 外，其他字段都允许用户修改并保存：

- `bootstrap.entry`
- `bootstrap.layer0`
- `bootstrap.layer1`
- `project.title`
- `project.title_zh`
- `project.version`
- `project.developer`
- `project.min_fw`
- `platforms.cartdark-os.app_icon`
- `display.width`
- `display.height`

## 5. 打开校验规则

IDE 打开 `.cart` 文件时必须校验：

1. 文件必须是合法 JSON。
2. 根节点必须是 JSON Object。
3. `format` 必须存在，且必须是支持的协议版本。
4. `bootstrap` 必须存在且为对象。
5. `bootstrap.entry` 必须存在，是字符串，指向存在的 `.lua` 文件。
6. `bootstrap.layer0` 必须存在，是字符串；空字符串表示未绑定，非空时应指向 `.layer` 文件。
7. `bootstrap.layer1` 必须存在，是字符串，且应指向 `.layer` 文件。
8. `project` 必须存在且为对象。
9. `project.id` 必须符合 `^0x[0-9A-Fa-f]{16}$`。
10. `project.title` 必须是字符串。
11. `project.title_zh` 必须是字符串。
12. `project.version` 必须是字符串。
13. `project.developer` 必须是字符串。
14. `project.min_fw` 必须是字符串。
15. `platforms.cartdark-os.app_icon` 必须存在，是字符串，且必须指向项目根目录下的图标文件。
16. `app_icon` 指向的图标必须是 `200x200`。
17. `display` 必须存在且为对象。
18. `display.width` 必须是正整数。
19. `display.height` 必须是正整数。

路径不存在、扩展名错误、图标尺寸错误和不支持的 `format` 都必须给出明确错误。

## 6. 新建项目默认值

新建项目时，IDE 从内置模板资源复制默认图标到 `assets/app_icon.png`，并默认生成如下 `.cart` 文件，其中 `project.id` 必须替换为随机 64-bit 十六进制 ID：

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
