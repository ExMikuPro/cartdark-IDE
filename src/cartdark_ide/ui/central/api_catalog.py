from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiItem:
    label: str
    insert_text: str
    kind: str = "function"
    detail: str = ""
    documentation: str = ""


def item(label: str, insert_text: str | None = None, kind: str = "function",
         detail: str = "", documentation: str = "") -> ApiItem:
    return ApiItem(
        label=label,
        insert_text=label if insert_text is None else insert_text,
        kind=kind,
        detail=detail,
        documentation=documentation,
    )


def lifecycle(name: str, args: str, documentation: str) -> ApiItem:
    return item(
        name,
        f"function {name}({args})\n    {{cursor}}\nend",
        "snippet",
        f"Lifecycle - function {name}({args})",
        documentation,
    )


LUA_KEYWORDS = [
    "and", "break", "do", "else", "elseif", "end", "false",
    "for", "function", "if", "in", "local", "nil",
    "not", "or", "repeat", "return", "then", "true", "until", "while",
]

LUA_BUILTINS = [
    "assert", "error", "ipairs", "next", "pairs", "pcall", "print",
    "rawequal", "rawget", "rawlen", "rawset", "select", "tonumber",
    "tostring", "type", "xpcall", "coroutine", "table", "string",
    "math", "utf8",
]

LUA_SPECIAL_NAMES = ["self"]

LUA_KEYWORD_ITEMS = [
    item(keyword, kind="keyword", detail="Lua keyword", documentation=f"Lua keyword: {keyword}.")
    for keyword in LUA_KEYWORDS
]

LUA_SNIPPETS = [
    item("if", "if condition then\n    {cursor}\nend", "snippet", "Lua if block", "Insert an if / then / end block."),
    item("ifelse", "if condition then\n    {cursor}\nelse\n    \nend", "snippet", "Lua if/else block", "Insert an if / else / end block."),
    item("fori", "for i = 1, n do\n    {cursor}\nend", "snippet", "Lua numeric for", "Insert a numeric for loop."),
    item("forpairs", "for k, v in pairs(t) do\n    {cursor}\nend", "snippet", "Lua pairs loop", "Iterate key/value pairs with pairs(t)."),
    item("foripairs", "for i, v in ipairs(t) do\n    {cursor}\nend", "snippet", "Lua ipairs loop", "Iterate index/value pairs with ipairs(t)."),
    item("while", "while condition do\n    {cursor}\nend", "snippet", "Lua while loop", "Insert a while / do / end block."),
    item("repeat", "repeat\n    {cursor}\nuntil condition", "snippet", "Lua repeat loop", "Insert a repeat / until loop."),
    item("func", "function name()\n    {cursor}\nend", "snippet", "Lua function", "Insert a function declaration."),
    item("localfunc", "local function name()\n    {cursor}\nend", "snippet", "Lua local function", "Insert a local function declaration."),
    item("table", "local name = {\n    {cursor}\n}", "snippet", "Lua table literal", "Insert a local table literal."),
]

LUA_BASE_API = [
    item("assert(v, message)", detail="assert(v, message)", documentation="Raise an error if v is false or nil."),
    item("error(message)", detail="error(message)", documentation="Raise a Lua error."),
    item("ipairs(t)", detail="ipairs(t)", documentation="Iterate array-style numeric keys."),
    item("next(table, index)", detail="next(table, index)", documentation="Return the next table key/value pair."),
    item("pairs(t)", detail="pairs(t)", documentation="Iterate all key/value pairs."),
    item("pcall(f, ...)", detail="pcall(f, ...)", documentation="Call a function in protected mode."),
    item("print(...)", detail="print(...)", documentation="Print values to the runtime console/log."),
    item("rawequal(v1, v2)", detail="rawequal(v1, v2)", documentation="Compare two values without metamethods."),
    item("rawget(table, index)", detail="rawget(table, index)", documentation="Read a table value without metamethods."),
    item("rawlen(v)", detail="rawlen(v)", documentation="Return raw length without metamethods."),
    item("rawset(table, index, value)", detail="rawset(table, index, value)", documentation="Write a table value without metamethods."),
    item("select(index, ...)", detail="select(index, ...)", documentation="Select values from varargs."),
    item("tonumber(e, base)", detail="tonumber(e, base)", documentation="Convert a value to a number."),
    item("tostring(v)", detail="tostring(v)", documentation="Convert a value to a string."),
    item("type(v)", detail="type(v)", documentation="Return the Lua type name for a value."),
    item("xpcall(f, msgh, ...)", detail="xpcall(f, msgh, ...)", documentation="Protected call with an error handler."),
]

LUA_STANDARD_MODULES = [
    item("coroutine", kind="module", detail="Lua coroutine library", documentation="Allowed Lua coroutine library."),
    item("table", kind="module", detail="Lua table library", documentation="Allowed Lua table library."),
    item("string", kind="module", detail="Lua string library", documentation="Allowed Lua string library."),
    item("math", kind="module", detail="Lua math library", documentation="Allowed Lua math library."),
    item("utf8", kind="module", detail="Lua utf8 library", documentation="Allowed Lua utf8 library."),
]

LIFECYCLE_SNIPPETS = [
    lifecycle("init", "self", "Called once when this script instance is initialized."),
    lifecycle("fixed_update", "self, dt", "Called on the fixed-step update tick."),
    lifecycle("update", "self, dt", "Called every frame with delta time in seconds."),
    lifecycle("late_update", "self, dt", "Called after the regular frame update."),
    lifecycle("final", "self", "Called before the script instance is destroyed."),
    lifecycle("on_input", "self, action_id, action", "Receives CartDark input actions and event payloads."),
    lifecycle("on_message", "self, message_id, message, sender", "Receives runtime messages for this script."),
    lifecycle("on_reload", "self", "Called after this script is reloaded."),
]

ACTION_EVENTS = [
    item("pressed", kind="constant", detail="input event", documentation="The action was pressed."),
    item("released", kind="constant", detail="input event", documentation="The action was released."),
    item("clicked", kind="constant", detail="input event", documentation="A tap/click style action completed."),
    item("changed", kind="constant", detail="input event", documentation="The action value changed."),
    item("moved", kind="constant", detail="input event", documentation="A pointer or movement action moved."),
]

SELF_FIELDS = [
    item("state", kind="field", detail="script state", documentation="Per-script mutable state table."),
    item("children", kind="field", detail="node children", documentation="UI / Drawable child nodes keyed by string id."),
]

GPIO_API = [
    item("count()", detail="gpio.count() -> number", documentation="Return the number of GPIO-capable pins."),
    item("list()", detail="gpio.list() -> table", documentation="Return available GPIO pin descriptors."),
    item("info(pin)", detail="gpio.info(pin) -> table", documentation="Return metadata for a GPIO pin."),
    item("setup(pin, config)", detail="gpio.setup(pin, config)", documentation="Configure a GPIO pin with a mode/options table."),
    item("read(pin)", detail="gpio.read(pin) -> value", documentation="Read the current value from a GPIO pin."),
    item("write(pin, value)", detail="gpio.write(pin, value)", documentation="Write a boolean or level value to a GPIO pin."),
    item("toggle(pin)", detail="gpio.toggle(pin)", documentation="Toggle a GPIO pin output value."),
    item("release(pin)", detail="gpio.release(pin)", documentation="Release IDE/runtime ownership of a GPIO pin."),
    item("pinMode(pin, mode)", detail="gpio.pinMode(pin, mode)", documentation="Arduino-style GPIO mode configuration alias."),
    item("digitalRead(pin)", detail="gpio.digitalRead(pin) -> value", documentation="Arduino-style digital read alias."),
    item("digitalWrite(pin, value)", detail="gpio.digitalWrite(pin, value)", documentation="Arduino-style digital write alias."),
    item("LOW", kind="constant", detail="gpio.LOW", documentation="Low GPIO logic level."),
    item("HIGH", kind="constant", detail="gpio.HIGH", documentation="High GPIO logic level."),
    item("OUTPUT", kind="constant", detail="gpio.OUTPUT", documentation="Push-pull output mode."),
    item("INPUT", kind="constant", detail="gpio.INPUT", documentation="Input mode."),
    item("INPUT_PULLUP", kind="constant", detail="gpio.INPUT_PULLUP", documentation="Input with pull-up resistor."),
    item("INPUT_PULLDOWN", kind="constant", detail="gpio.INPUT_PULLDOWN", documentation="Input with pull-down resistor."),
    item("OUTPUT_OPEN_DRAIN", kind="constant", detail="gpio.OUTPUT_OPEN_DRAIN", documentation="Open-drain output mode."),
    item("ANALOG", kind="constant", detail="gpio.ANALOG", documentation="Analog pin mode."),
    item("RISING", kind="constant", detail="gpio.RISING", documentation="Rising edge trigger."),
    item("FALLING", kind="constant", detail="gpio.FALLING", documentation="Falling edge trigger."),
    item("CHANGE", kind="constant", detail="gpio.CHANGE", documentation="Any edge trigger."),
    item("LOW_LEVEL", kind="constant", detail="gpio.LOW_LEVEL", documentation="Low-level trigger."),
    item("HIGH_LEVEL", kind="constant", detail="gpio.HIGH_LEVEL", documentation="High-level trigger."),
    item("SPEED_LOW", kind="constant", detail="gpio.SPEED_LOW", documentation="Low GPIO output speed."),
    item("SPEED_MEDIUM", kind="constant", detail="gpio.SPEED_MEDIUM", documentation="Medium GPIO output speed."),
    item("SPEED_HIGH", kind="constant", detail="gpio.SPEED_HIGH", documentation="High GPIO output speed."),
]

PWM_API = [
    item("count()", detail="pwm.count() -> number", documentation="Return the number of PWM-capable pins."),
    item("list()", detail="pwm.list() -> table", documentation="Return available PWM pin descriptors."),
    item("info(pin)", detail="pwm.info(pin) -> table", documentation="Return metadata for a PWM pin."),
    item("setup(pin, config)", detail="pwm.setup(pin, config)", documentation="Configure PWM output on a pin."),
    item("write(pin, duty)", detail="pwm.write(pin, duty)", documentation="Write PWM duty value to a pin."),
    item("read(pin)", detail="pwm.read(pin) -> duty", documentation="Read the current PWM duty value."),
    item("set_freq(pin, freq)", detail="pwm.set_freq(pin, freq)", documentation="Set PWM frequency for a pin."),
    item("get_freq(pin)", detail="pwm.get_freq(pin) -> number", documentation="Get PWM frequency for a pin."),
    item("stop(pin)", detail="pwm.stop(pin)", documentation="Stop PWM output on a pin."),
    item("release(pin)", detail="pwm.release(pin)", documentation="Release PWM ownership of a pin."),
    item("MIN", kind="constant", detail="pwm.MIN", documentation="Minimum PWM duty value."),
    item("MAX", kind="constant", detail="pwm.MAX", documentation="Maximum PWM duty value."),
    item("DEFAULT_FREQ", kind="constant", detail="pwm.DEFAULT_FREQ", documentation="Default PWM frequency."),
    item("POLARITY_HIGH", kind="constant", detail="pwm.POLARITY_HIGH", documentation="Active-high PWM polarity."),
    item("POLARITY_LOW", kind="constant", detail="pwm.POLARITY_LOW", documentation="Active-low PWM polarity."),
]

TIM_API = [
    item("us()", detail="tim.us() -> number", documentation="Return a monotonic microsecond timer value."),
    item("delay_us(us)", detail="tim.delay_us(us)", documentation="Busy-wait for the given number of microseconds."),
]

RNG_API = [
    item("u32()", detail="rng.u32() -> number", documentation="Return a random unsigned 32-bit integer."),
    item("bytes(n)", detail="rng.bytes(n) -> string", documentation="Return n random bytes."),
]

CRC_API = [
    item("crc32(data)", detail="crc.crc32(data) -> number", documentation="Compute CRC-32 for data."),
    item("crc32_hex(data)", detail="crc.crc32_hex(data) -> string", documentation="Compute CRC-32 and return hexadecimal text."),
]

DELAY_API = [
    item("ms(ms)", detail="delay.ms(ms)", documentation="Sleep or wait for the given number of milliseconds."),
]

TABLE_API = [
    item("concat(list, sep, i, j)", detail="table.concat(list, sep, i, j)", documentation="Concatenate list elements into a string."),
    item("insert(list, pos, value)", detail="table.insert(list, pos, value)", documentation="Insert a value into a list."),
    item("move(a1, f, e, t, a2)", detail="table.move(a1, f, e, t, a2)", documentation="Move table elements between ranges."),
    item("pack(...)", detail="table.pack(...)", documentation="Pack values into a table with field n."),
    item("remove(list, pos)", detail="table.remove(list, pos)", documentation="Remove a value from a list."),
    item("sort(list, comp)", detail="table.sort(list, comp)", documentation="Sort a list in place."),
    item("unpack(list, i, j)", detail="table.unpack(list, i, j)", documentation="Return list elements from i to j."),
]

STRING_API = [
    item("byte(s, i, j)", detail="string.byte(s, i, j)", documentation="Return internal byte values for characters."),
    item("char(...)", detail="string.char(...)", documentation="Create a string from byte values."),
    item("dump(function)", detail="string.dump(function)", documentation="Return binary representation of a function."),
    item("find(s, pattern, init, plain)", detail="string.find(s, pattern, init, plain)", documentation="Find a pattern in a string."),
    item("format(formatstring, ...)", detail="string.format(formatstring, ...)", documentation="Format values into a string."),
    item("gmatch(s, pattern)", detail="string.gmatch(s, pattern)", documentation="Iterate pattern matches."),
    item("gsub(s, pattern, repl, n)", detail="string.gsub(s, pattern, repl, n)", documentation="Replace pattern matches."),
    item("len(s)", detail="string.len(s)", documentation="Return string length."),
    item("lower(s)", detail="string.lower(s)", documentation="Convert to lowercase."),
    item("match(s, pattern, init)", detail="string.match(s, pattern, init)", documentation="Return the first pattern match."),
    item("rep(s, n, sep)", detail="string.rep(s, n, sep)", documentation="Repeat a string."),
    item("reverse(s)", detail="string.reverse(s)", documentation="Reverse a string."),
    item("sub(s, i, j)", detail="string.sub(s, i, j)", documentation="Return a substring."),
    item("upper(s)", detail="string.upper(s)", documentation="Convert to uppercase."),
]

MATH_API = [
    item("abs(x)", detail="math.abs(x)", documentation="Return absolute value."),
    item("acos(x)", detail="math.acos(x)", documentation="Return arc cosine."),
    item("asin(x)", detail="math.asin(x)", documentation="Return arc sine."),
    item("atan(y, x)", detail="math.atan(y, x)", documentation="Return arc tangent."),
    item("ceil(x)", detail="math.ceil(x)", documentation="Round upward."),
    item("cos(x)", detail="math.cos(x)", documentation="Return cosine."),
    item("deg(x)", detail="math.deg(x)", documentation="Convert radians to degrees."),
    item("exp(x)", detail="math.exp(x)", documentation="Return e raised to x."),
    item("floor(x)", detail="math.floor(x)", documentation="Round downward."),
    item("fmod(x, y)", detail="math.fmod(x, y)", documentation="Return remainder of division."),
    item("huge", kind="constant", detail="math.huge", documentation="Floating-point infinity value."),
    item("log(x, base)", detail="math.log(x, base)", documentation="Return logarithm."),
    item("max(...)", detail="math.max(...)", documentation="Return maximum argument."),
    item("maxinteger", kind="constant", detail="math.maxinteger", documentation="Maximum integer value."),
    item("min(...)", detail="math.min(...)", documentation="Return minimum argument."),
    item("mininteger", kind="constant", detail="math.mininteger", documentation="Minimum integer value."),
    item("modf(x)", detail="math.modf(x)", documentation="Split into integer and fractional parts."),
    item("pi", kind="constant", detail="math.pi", documentation="Pi constant."),
    item("rad(x)", detail="math.rad(x)", documentation="Convert degrees to radians."),
    item("random(m, n)", detail="math.random(m, n)", documentation="Return a pseudo-random number."),
    item("randomseed(x)", detail="math.randomseed(x)", documentation="Seed pseudo-random generator."),
    item("sin(x)", detail="math.sin(x)", documentation="Return sine."),
    item("sqrt(x)", detail="math.sqrt(x)", documentation="Return square root."),
    item("tan(x)", detail="math.tan(x)", documentation="Return tangent."),
    item("tointeger(x)", detail="math.tointeger(x)", documentation="Convert to integer when possible."),
    item("type(x)", detail="math.type(x)", documentation="Return integer/float subtype."),
    item("ult(m, n)", detail="math.ult(m, n)", documentation="Unsigned less-than comparison."),
]

COROUTINE_API = [
    item("create(f)", detail="coroutine.create(f)", documentation="Create a coroutine."),
    item("isyieldable()", detail="coroutine.isyieldable()", documentation="Return whether the current context can yield."),
    item("resume(co, ...)", detail="coroutine.resume(co, ...)", documentation="Resume a coroutine."),
    item("running()", detail="coroutine.running()", documentation="Return the running coroutine."),
    item("status(co)", detail="coroutine.status(co)", documentation="Return coroutine status."),
    item("wrap(f)", detail="coroutine.wrap(f)", documentation="Create a coroutine wrapper function."),
    item("yield(...)", detail="coroutine.yield(...)", documentation="Yield from a coroutine."),
]

UTF8_API = [
    item("char(...)", detail="utf8.char(...)", documentation="Create UTF-8 characters from codepoints."),
    item("charpattern", kind="constant", detail="utf8.charpattern", documentation="Pattern matching one UTF-8 byte sequence."),
    item("codepoint(s, i, j)", detail="utf8.codepoint(s, i, j)", documentation="Return codepoints for a string range."),
    item("codes(s)", detail="utf8.codes(s)", documentation="Iterate UTF-8 codepoints."),
    item("len(s, i, j)", detail="utf8.len(s, i, j)", documentation="Return UTF-8 codepoint count."),
    item("offset(s, n, i)", detail="utf8.offset(s, n, i)", documentation="Return byte offset for a UTF-8 codepoint."),
]

NODE_API = [
    item("get(layer, id)", detail="node.get(layer, id) -> handle", documentation="Get a UI / Drawable node handle by layer and string id."),
    item("get(id)", detail="node.get(id) -> handle", documentation="Get a UI / Drawable node handle by string id."),
    item("type(handle)", detail="node.type(handle) -> string", documentation="Return the runtime node type for a handle."),
    item("set_hidden(handle, hidden)", detail="node.set_hidden(handle, hidden)", documentation="Show or hide a node."),
    item("set_rect(handle, x, y, w, h)", detail="node.set_rect(handle, x, y, w, h)", documentation="Update node rectangle geometry."),
    item("set_text(handle, text)", detail="node.set_text(handle, text)", documentation="Set text on text and button nodes."),
    item("set_value(handle, value)", detail="node.set_value(handle, value)", documentation="Set slider node value."),
    item("get_value(handle)", detail="node.get_value(handle) -> value", documentation="Get slider node value."),
]

LAYER_API = [
    item("enable(name_or_id)", detail="layer.enable(name_or_id)", documentation="Enable a display layer by name or id."),
    item("disable(name_or_id)", detail="layer.disable(name_or_id)", documentation="Disable a display layer by name or id."),
    item("set_enabled(name_or_id, enabled)", detail="layer.set_enabled(name_or_id, enabled)", documentation="Set layer enabled state."),
    item("is_enabled(name_or_id)", detail="layer.is_enabled(name_or_id) -> bool", documentation="Return whether a layer is enabled."),
    item("set_alpha(name_or_id, alpha)", detail="layer.set_alpha(name_or_id, alpha)", documentation="Set layer alpha opacity."),
    item("get_alpha(name_or_id)", detail="layer.get_alpha(name_or_id) -> number", documentation="Get layer alpha opacity."),
]

UI_API = [
    item("button(config)", detail="ui.button(config)", documentation="Create a button using the first-version LVGL default styling."),
    item("slider(config)", detail="ui.slider(config)", documentation="Create a slider using the first-version LVGL default styling."),
    item("image(config)", detail="ui.image(config)", documentation="Create an image node from config."),
    item("find(self, id)", detail="ui.find(self, id) -> handle", documentation="Find a UI node under this script by id."),
    item("patch(self, id, patch)", detail="ui.patch(self, id, patch)", documentation="Legacy / discouraged patch helper; prefer node.* APIs where possible."),
]

MODULE_APIS = {
    "gpio": GPIO_API,
    "pwm": PWM_API,
    "tim": TIM_API,
    "rng": RNG_API,
    "crc": CRC_API,
    "delay": DELAY_API,
    "node": NODE_API,
    "layer": LAYER_API,
    "ui": UI_API,
    "table": TABLE_API,
    "string": STRING_API,
    "math": MATH_API,
    "coroutine": COROUTINE_API,
    "utf8": UTF8_API,
    "self": SELF_FIELDS,
    "action": [
        item("event", kind="field", detail="action.event", documentation="Input event name such as pressed, released, clicked, changed, or moved."),
    ],
}

GLOBAL_APIS = [
    item("gpio", kind="module", detail="GPIO module", documentation="CartDark GPIO access module."),
    item("pwm", kind="module", detail="PWM module", documentation="CartDark PWM output module."),
    item("tim", kind="module", detail="Timer module", documentation="Microsecond timer helpers."),
    item("rng", kind="module", detail="Random module", documentation="Hardware/random byte helpers."),
    item("crc", kind="module", detail="CRC module", documentation="CRC-32 helpers."),
    item("node", kind="module", detail="Node module", documentation="UI / Drawable node lookup and mutation helpers."),
    item("layer", kind="module", detail="Layer module", documentation="LTDC layer enable/alpha helpers."),
    item("ui", kind="module", detail="UI module", documentation="First-version UI node creation helpers."),
    item("delay(ms)", kind="function", detail="delay(ms)", documentation="Wait for the given number of milliseconds."),
    item("pinMode(pin, mode)", kind="function", detail="pinMode(pin, mode)", documentation="Global Arduino-style GPIO mode alias."),
    item("digitalRead(pin)", kind="function", detail="digitalRead(pin)", documentation="Global Arduino-style GPIO read alias."),
    item("digitalWrite(pin, value)", kind="function", detail="digitalWrite(pin, value)", documentation="Global Arduino-style GPIO write alias."),
]

LUA_WORD_COMPLETIONS = [
    *LUA_SNIPPETS,
    *LUA_KEYWORD_ITEMS,
    *LUA_BASE_API,
    *LUA_STANDARD_MODULES,
]

UI_CONFIG_FIELDS = {
    "button": [
        item("id", kind="field", detail="button id", documentation="String id for the node."),
        item("rect", kind="field", detail="button rect", documentation="Rectangle tuple/table for the node."),
        item("x", kind="field", detail="button x", documentation="X coordinate."),
        item("y", kind="field", detail="button y", documentation="Y coordinate."),
        item("w", kind="field", detail="button width", documentation="Width."),
        item("h", kind="field", detail="button height", documentation="Height."),
        item("hidden", kind="field", detail="button hidden", documentation="Initial hidden state."),
        item("input", kind="field", detail="button input", documentation="Input action id emitted by this button."),
        item("text", kind="field", detail="button text", documentation="Button label text."),
    ],
    "slider": [
        item("id", kind="field", detail="slider id", documentation="String id for the node."),
        item("rect", kind="field", detail="slider rect", documentation="Rectangle tuple/table for the node."),
        item("x", kind="field", detail="slider x", documentation="X coordinate."),
        item("y", kind="field", detail="slider y", documentation="Y coordinate."),
        item("w", kind="field", detail="slider width", documentation="Width."),
        item("h", kind="field", detail="slider height", documentation="Height."),
        item("hidden", kind="field", detail="slider hidden", documentation="Initial hidden state."),
        item("input", kind="field", detail="slider input", documentation="Input action id emitted by this slider."),
        item("range", kind="field", detail="slider range", documentation="Slider min/max range."),
        item("value", kind="field", detail="slider value", documentation="Initial slider value."),
    ],
    "image": [
        item("id", kind="field", detail="image id", documentation="String id for the node."),
        item("rect", kind="field", detail="image rect", documentation="Rectangle tuple/table for the node."),
        item("x", kind="field", detail="image x", documentation="X coordinate."),
        item("y", kind="field", detail="image y", documentation="Y coordinate."),
        item("w", kind="field", detail="image width", documentation="Width."),
        item("h", kind="field", detail="image height", documentation="Height."),
        item("hidden", kind="field", detail="image hidden", documentation="Initial hidden state."),
        item("input", kind="field", detail="image input", documentation="Input action id emitted by this image."),
        item("src", kind="field", detail="image src", documentation="Image resource path."),
        item("region", kind="field", detail="image region", documentation="Image atlas/source region."),
    ],
}

CART_KEYS = [
    item("format", kind="field"), item("bootstrap", kind="field"),
    item("entry", kind="field"), item("layer0", kind="field"),
    item("layer1", kind="field"), item("project", kind="field"),
    item("id", kind="field"), item("title", kind="field"),
    item("title_zh", kind="field"), item("version", kind="field"),
    item("developer", kind="field"), item("min_fw", kind="field"),
    item("platforms", kind="field"), item("cartdark-os", kind="field"),
    item("app_icon", kind="field"), item("display", kind="field"),
    item("width", kind="field"), item("height", kind="field"),
]

LAYER_KEYS = [
    item("canvas", kind="field"), item("node", kind="field"),
    item("id", kind="field"), item("type", kind="field"),
    item("name", kind="field"), item("path", kind="field"),
    item("width", kind="field"), item("height", kind="field"),
    item("position", kind="field"), item("x", kind="field"),
    item("y", kind="field"),
]

INPUT_BINDING_KEYS = [
    item("format", kind="field"), item("version", kind="field"),
    item("name", kind="field"), item("pin_triggers", kind="field"),
    item("touch_triggers", kind="field"), item("gamepad_triggers", kind="field"),
    item("input", kind="field"), item("action", kind="field"),
    item("event", kind="field"),
]


def lifecycle_names() -> list[str]:
    return [entry.label.split("(", 1)[0] for entry in LIFECYCLE_SNIPPETS]


def module_names() -> list[str]:
    return [name for name in MODULE_APIS if name not in {"self", "action"}]


def api_symbols() -> list[str]:
    symbols: list[str] = []
    for module, entries in MODULE_APIS.items():
        if module in {"self", "action"}:
            continue
        for entry in entries:
            head = entry.label.split("(", 1)[0]
            symbols.append(f"{module}.{head}")
    return symbols


def hover_text(symbol: str) -> str:
    entry = API_BY_SYMBOL.get(symbol)
    if entry is None:
        return ""
    parts = [f"<b>{symbol}</b>"]
    if entry.detail:
        parts.append(entry.detail)
    if entry.documentation:
        parts.append(entry.documentation)
    return "<br>".join(parts)


def _build_api_index() -> dict[str, ApiItem]:
    index: dict[str, ApiItem] = {}
    for entry in LIFECYCLE_SNIPPETS:
        name = entry.label.split("(", 1)[0]
        index[name] = entry
    for entry in GLOBAL_APIS:
        name = entry.label.split("(", 1)[0]
        index[name] = entry
    for module, entries in MODULE_APIS.items():
        for entry in entries:
            name = entry.label.split("(", 1)[0]
            index.setdefault(f"{module}.{name}", entry)
    return index


API_BY_SYMBOL = _build_api_index()
