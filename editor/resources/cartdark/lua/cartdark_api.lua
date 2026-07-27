-- Copyright 2026 ExMikuPro
-- CartDark Studio firmware API declarations for documentation and tooling.
-- This file is not linked into a cartridge.

---@meta

function init() end
function fixed_update(dt) end
function update(dt) end
function late_update(dt) end
function on_input(action_id, action) end
function on_message(message_id, message, sender) end
function on_reload() end
function final() end

ui = {}
gpio = {}
pwm = {}
tim = {}
rng = {}
crc = {}

---@param milliseconds integer
function delay(milliseconds) end

-- Firmware note: io, os, debug, and package are unavailable at runtime.
