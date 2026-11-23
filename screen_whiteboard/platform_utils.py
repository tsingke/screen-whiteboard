# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""Qt 初始化与平台适配。"""

from __future__ import annotations

import copy
import sys
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtWidgets import QApplication


def configure_high_dpi() -> None:
    """启用逐显示器 DPI 缩放。必须在 QApplication 创建之前调用。"""
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass


def pick_font_family(configured: str) -> str:
    """优先使用配置字体，找不到时退回系统中常见的中文字体。"""
    try:
        families = set(QFontDatabase.families())
    except Exception:
        return configured
    candidates = [
        configured,
        "PingFang SC" if sys.platform == "darwin" else "",
        "Microsoft YaHei UI" if sys.platform == "win32" else "",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "Arial",
    ]
    for family in candidates:
        if family and family in families:
            return family
    return configured


def copy_settings(settings: Any, **overrides: Any) -> Any:
    """基于现有配置生成带覆盖项的新配置（避免就地修改）。"""
    clone = copy.deepcopy(settings)
    for key, value in overrides.items():
        if value is not None and hasattr(clone, key):
            setattr(clone, key, value)
    clone.validate()
    return clone
