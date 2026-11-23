# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""跨平台屏幕截取。

Windows 使用 Pillow 的 ImageGrab；macOS 优先用 screencapture；
Linux 依次尝试 ImageGrab 以及常见的截图命令行工具。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


class ScreenCaptureError(RuntimeError):
    """截屏失败，调用方应提示用户检查权限或依赖。"""


@dataclass
class Capture:
    image: Image.Image
    width: int
    height: int
    origin_x: int = 0
    origin_y: int = 0


def _fit(image: Image.Image, width: int, height: int) -> Image.Image:
    """把截图缩放到 Tk 的逻辑像素尺寸，保证坐标一一对应。"""
    image = image.convert("RGB")
    if width > 0 and height > 0 and image.size != (width, height):
        image = image.resize((width, height), Image.LANCZOS)
    return image


def _windows_virtual_metrics() -> tuple[int, int, int, int]:
    if sys.platform != "win32":
        return 0, 0, 0, 0
    try:
        import ctypes

        user32 = ctypes.windll.user32
        return (
            int(user32.GetSystemMetrics(76)),  # SM_XVIRTUALSCREEN
            int(user32.GetSystemMetrics(77)),  # SM_YVIRTUALSCREEN
            int(user32.GetSystemMetrics(78)),  # SM_CXVIRTUALSCREEN
            int(user32.GetSystemMetrics(79)),  # SM_CYVIRTUALSCREEN
        )
    except Exception:
        return 0, 0, 0, 0


def _grab_windows(width: int, height: int, all_monitors: bool) -> Capture:
    from PIL import ImageGrab

    try:
        image = ImageGrab.grab(all_screens=all_monitors)
    except Exception as exc:  # pragma: no cover - 取决于本机环境
        raise ScreenCaptureError(f"Windows 截屏失败：{exc}") from exc

    origin_x = origin_y = 0
    target_w, target_h = width, height
    if all_monitors:
        origin_x, origin_y, vw, vh = _windows_virtual_metrics()
        if vw > 0 and vh > 0:
            target_w, target_h = vw, vh
            image = _fit(image, vw, vh)
    else:
        image = _fit(image, width, height)
    return Capture(image=image, width=target_w, height=target_h,
                   origin_x=origin_x, origin_y=origin_y)


def _temp_png() -> Path:
    fd, name = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    return Path(name)


def _grab_macos(width: int, height: int) -> Capture:
    tmp = _temp_png()
    try:
        result = subprocess.run(
            ["screencapture", "-x", "-t", "png", str(tmp)],
            capture_output=True,
        )
        if result.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
            with Image.open(tmp) as img:
                image = img.copy()
            return Capture(_fit(image, width, height), width, height,
                           origin_x=0, origin_y=0)
    finally:
        tmp.unlink(missing_ok=True)

    # screencapture 不可用时退回 Pillow
    try:
        from PIL import ImageGrab

        image = ImageGrab.grab()
        return Capture(_fit(image, width, height), width, height,
                       origin_x=0, origin_y=0)
    except Exception as exc:
        raise ScreenCaptureError(
            "macOS 截屏失败。请到「系统设置 → 隐私与安全性 → 屏幕录制」"
            "为终端或本程序授权后重试。"
        ) from exc


def _grab_linux(width: int, height: int) -> Capture:
    try:
        from PIL import ImageGrab

        image = ImageGrab.grab()
        return Capture(_fit(image, width, height), width, height,
                       origin_x=0, origin_y=0)
    except Exception:
        pass

    commands = [
        ("gnome-screenshot", ["-f"]),
        ("spectacle", ["-b", "-n", "-o"]),
        ("scrot", []),
        ("grim", []),
        ("import", ["-window", "root"]),
    ]
    for name, prefix in commands:
        exe = shutil.which(name)
        if not exe:
            continue
        tmp = _temp_png()
        try:
            cmd = [exe] + prefix + [str(tmp)]
            if name == "import":
                cmd = [exe, "-window", "root", str(tmp)]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
                with Image.open(tmp) as img:
                    image = img.copy()
                return Capture(_fit(image, width, height), width, height,
                               origin_x=0, origin_y=0)
        except Exception:
            continue
        finally:
            tmp.unlink(missing_ok=True)

    raise ScreenCaptureError(
        "Linux 截屏失败。请安装 gnome-screenshot、spectacle、scrot、grim "
        "或 ImageMagick 之一，并确认当前桌面会话允许截图。"
    )


def grab_screen(width: int, height: int, all_monitors: bool = False) -> Capture:
    """截取屏幕。

    width/height 为 Tk 报告的逻辑像素尺寸。返回值中的 image 已缩放到
    对应尺寸，画布坐标与图片坐标一致。
    """
    if sys.platform == "win32":
        return _grab_windows(width, height, all_monitors)
    if sys.platform == "darwin":
        return _grab_macos(width, height)
    return _grab_linux(width, height)
