# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""平台相关的初始化。"""

from __future__ import annotations

import copy
import sys
import tkinter as tk
from typing import Any, Optional


def enable_dpi_awareness() -> Optional[str]:
    """在 Windows 上启用高 DPI 感知。

    必须在创建 Tk 根窗口之前调用。返回实际生效的方式，便于日志输出。
    """
    if sys.platform != "win32":
        return None

    try:
        import ctypes

        user32 = ctypes.windll.user32
        set_context = getattr(user32, "SetProcessDpiAwarenessContext", None)
        if set_context is not None:
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
            if set_context(ctypes.c_void_p(-4)):
                return "per-monitor-v2"
    except Exception:
        pass

    try:
        import ctypes

        shcore = ctypes.windll.shcore
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        if shcore.SetProcessDpiAwareness(2) == 0:
            return "per-monitor"
    except Exception:
        pass

    try:
        import ctypes

        if ctypes.windll.user32.SetProcessDPIAware():
            return "system"
    except Exception:
        pass

    return None


def screen_metrics(root: tk.Misc) -> tuple[int, int]:
    """返回主屏幕的逻辑尺寸。"""
    return int(root.winfo_screenwidth()), int(root.winfo_screenheight())


def copy_settings(settings: Any, **overrides: Any) -> Any:
    """基于现有配置生成带覆盖项的新配置（避免就地修改）。"""
    clone = copy.deepcopy(settings)
    for key, value in overrides.items():
        if value is not None and hasattr(clone, key):
            setattr(clone, key, value)
    clone.validate()
    return clone
