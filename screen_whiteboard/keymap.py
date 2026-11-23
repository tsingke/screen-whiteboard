# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""键盘事件到动作的纯函数映射，便于单元测试。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

WIDTH_KEYS = "123456789"


class ActionType(Enum):
    NONE = "none"
    COLOR = "color"
    WIDTH = "width"
    CLEAR = "clear"
    SAVE = "save"
    CLOSE = "close"
    UNDO = "undo"


@dataclass(frozen=True)
class Action:
    type: ActionType
    value: Any = None


NONE = Action(ActionType.NONE)
CLEAR = Action(ActionType.CLEAR)
SAVE = Action(ActionType.SAVE)
CLOSE = Action(ActionType.CLOSE)
UNDO = Action(ActionType.UNDO)


def resolve_key(
    char: Optional[str],
    keysym: Optional[str],
    ctrl: bool = False,
    colors: Optional[Dict[str, str]] = None,
) -> Action:
    """根据按键字符、符号与 Ctrl 状态给出动作。

    Esc 退出标注模式；Ctrl+Z 撤销；Ctrl+S 保存。
    小写字母键用于切换颜色与工具。
    """
    colors = colors or {}
    key = (char or "").lower()
    sym = (keysym or "").lower()

    if sym == "escape":
        return CLOSE
    if ctrl and sym == "z":
        return UNDO
    if ctrl and sym == "s":
        return SAVE
    if key in colors:
        return Action(ActionType.COLOR, colors[key])
    if key in WIDTH_KEYS:
        return Action(ActionType.WIDTH, int(key))
    if key == "c":
        return CLEAR
    if key == "s":
        return SAVE
    return NONE
