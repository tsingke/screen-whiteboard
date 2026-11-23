# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""基于 Qt 的屏幕截取。

Qt 的 grabWindow 直接返回物理像素，并保留屏幕的 devicePixelRatio，
因此不需要任何缩放，文字与细线在高分屏上依然清晰。
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Tuple

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QScreen


class ScreenCaptureError(RuntimeError):
    """截屏失败，调用方应提示用户检查权限。"""


@dataclass
class Capture:
    image: QImage
    width: int          # 逻辑宽度
    height: int         # 逻辑高度
    origin_x: int
    origin_y: int
    dpr: float


def screen_capture_allowed() -> bool:
    """macOS 上检查屏幕录制权限；其他平台始终返回 True。"""
    if sys.platform != "darwin":
        return True
    try:
        cg = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
        return bool(cg.CGPreflightScreenCaptureAccess())
    except Exception:
        return True


def request_screen_capture_access() -> None:
    """触发 macOS 的屏幕录制授权请求（系统只会在首次弹窗）。"""
    if sys.platform != "darwin":
        return
    try:
        cg = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cg.CGRequestScreenCaptureAccess.restype = ctypes.c_bool
        cg.CGRequestScreenCaptureAccess()
    except Exception:
        pass


def open_screen_recording_settings() -> None:
    if sys.platform != "darwin":
        return
    subprocess.Popen(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ]
    )


def _grab_screen_image(screen: QScreen) -> Tuple[QImage, float]:
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        raise ScreenCaptureError(
            "无法读取屏幕画面。请检查系统的屏幕录制权限后重试。"
        )
    image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32_Premultiplied)
    geometry = screen.geometry()
    dpr = screen.devicePixelRatio() or 1.0
    if geometry.width() > 0:
        measured = image.width() / float(geometry.width())
        if measured > 0.1:
            dpr = measured
    image.setDevicePixelRatio(dpr)
    return image, dpr


def grab_screen(screen: QScreen, all_monitors: bool = False) -> Capture:
    """截取指定屏幕；all_monitors 为 True 时拼接整个虚拟桌面。"""
    if all_monitors:
        return _grab_virtual_desktop()
    image, dpr = _grab_screen_image(screen)
    geometry = screen.geometry()
    return Capture(
        image=image,
        width=geometry.width(),
        height=geometry.height(),
        origin_x=geometry.x(),
        origin_y=geometry.y(),
        dpr=dpr,
    )


def _grab_virtual_desktop() -> Capture:
    screens: List[QScreen] = QGuiApplication.screens()
    if not screens:
        raise ScreenCaptureError("没有检测到可用显示器。")

    virtual = screens[0].geometry()
    for screen in screens[1:]:
        virtual = virtual.united(screen.geometry())

    dpr = max((s.devicePixelRatio() or 1.0) for s in screens)
    background = QColor(0, 0, 0)
    canvas = QImage(
        max(1, int(round(virtual.width() * dpr))),
        max(1, int(round(virtual.height() * dpr))),
        QImage.Format_ARGB32_Premultiplied,
    )
    canvas.fill(background)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    for screen in screens:
        image, _ = _grab_screen_image(screen)
        geometry = screen.geometry()
        target = QRectF(
            (geometry.x() - virtual.x()) * dpr,
            (geometry.y() - virtual.y()) * dpr,
            geometry.width() * dpr,
            geometry.height() * dpr,
        )
        painter.drawImage(target, image)
    painter.end()

    canvas.setDevicePixelRatio(dpr)
    return Capture(
        image=canvas,
        width=virtual.width(),
        height=virtual.height(),
        origin_x=virtual.x(),
        origin_y=virtual.y(),
        dpr=dpr,
    )
