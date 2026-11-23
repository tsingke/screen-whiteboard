# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""应用入口：悬浮按钮 + 标注层调度。"""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import messagebox
from typing import Optional, Sequence

from . import __version__
from .capture import ScreenCaptureError, grab_screen
from .config import (
    Settings,
    default_base_dir,
    default_config_path,
    load_settings,
    save_settings,
)
from .help import HelpWindow
from .overlay import AnnotationOverlay
from .platform_utils import copy_settings, enable_dpi_awareness, screen_metrics


class WhiteboardApp:
    """管理右上角悬浮按钮与全屏标注层。"""

    def __init__(self, root: tk.Tk, settings: Settings) -> None:
        self.root = root
        self.settings = settings
        self._drag_offset: Optional[tuple[int, int]] = None
        self._busy = False

        self._build_launcher()

    def _build_launcher(self) -> None:
        s = self.settings
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=s.launcher_bg)

        self.button = tk.Button(
            self.root,
            text=s.launcher_text,
            command=self.start_annotation,
            bg=s.launcher_bg,
            fg=s.launcher_fg,
            activebackground=s.launcher_active_bg,
            activeforeground=s.launcher_fg,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=s.launcher_padx,
            pady=s.launcher_pady,
            font=(s.launcher_font_family, s.launcher_font_size, "bold"),
            cursor="hand2",
        )
        self.button.pack()

        self.button.bind("<ButtonPress-1>", self._on_press)
        self.button.bind("<B1-Motion>", self._on_drag)
        self.button.bind("<ButtonRelease-1>", self._on_release)
        for sequence in ("<ButtonRelease-2>", "<ButtonRelease-3>"):
            self.button.bind(sequence, lambda _event: self.quit())

        self.root.update_idletasks()
        self.root.geometry(f"-{s.offset_x}+{s.offset_y}")

    # ------------------------------------------------------------------ 拖动

    def _on_press(self, event: tk.Event) -> None:
        self._drag_offset = (
            event.x_root - self.root.winfo_rootx(),
            event.y_root - self.root.winfo_rooty(),
        )

    def _on_drag(self, event: tk.Event) -> None:
        if self._drag_offset is None:
            return
        dx, dy = self._drag_offset
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _on_release(self, _event: tk.Event) -> None:
        self._drag_offset = None

    # ------------------------------------------------------------------ 标注

    def start_annotation(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.root.withdraw()
        self.root.update_idletasks()
        # 留一点时间让桌面重绘，避免截到按钮残影
        delay = int(max(0.0, self.settings.hide_delay) * 1000)
        self.root.after(delay, self._open_overlay)

    def _open_overlay(self) -> None:
        try:
            width, height = screen_metrics(self.root)
            capture = grab_screen(width, height, all_monitors=self.settings.all_monitors)
            overlay = AnnotationOverlay(self.root, capture, self.settings)
            overlay.wait()
        except ScreenCaptureError as exc:
            messagebox.showerror("无法开始标注", str(exc))
        except tk.TclError as exc:
            messagebox.showerror("界面错误", f"无法创建标注窗口：\n{exc}")
        except Exception as exc:  # 尽量不让异常直接杀掉进程
            messagebox.showerror("出错了", f"标注模式启动失败：\n{exc}")
        finally:
            self._busy = False
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.attributes("-topmost", True)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------ 退出

    def quit(self) -> None:
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="screen-whiteboard",
        description="开源屏幕白板教学工具：悬浮按钮 + 全屏标注 + 截图保存。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", type=Path, default=None, help="配置文件路径（JSON）")
    parser.add_argument("--offset-x", type=int, default=None, help="按钮距离屏幕右侧的像素")
    parser.add_argument("--offset-y", type=int, default=None, help="按钮距离屏幕顶部的像素")
    parser.add_argument("--save-dir", type=str, default=None, help="截图默认保存目录")
    parser.add_argument(
        "--all-monitors",
        action="store_true",
        default=None,
        help="截取全部显示器（默认仅主屏）",
    )
    parser.add_argument("--no-help", action="store_true", help="首次启动时不显示使用说明")
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="打印当前生效配置后退出",
    )
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="把当前生效配置写入默认位置后退出",
    )
    return parser.parse_args(argv)


def _first_run_marker() -> Path:
    return default_base_dir() / "help_shown"


def _maybe_show_help(root: tk.Tk, settings: Settings) -> None:
    if not settings.help_on_first_run:
        return
    marker = _first_run_marker()
    if marker.exists():
        return
    try:
        window = HelpWindow(root, settings)
        window.wait_window()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("1\n", encoding="utf-8")
    except OSError:
        # 配置目录不可写时静默跳过，不影响主功能。
        pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    settings = load_settings(args.config)
    settings = copy_settings(
        settings,
        offset_x=args.offset_x,
        offset_y=args.offset_y,
        save_dir=args.save_dir,
        all_monitors=args.all_monitors,
        help_on_first_run=False if args.no_help else None,
    )

    if args.print_config:
        print(json.dumps(asdict(settings), ensure_ascii=False, indent=2))
        return 0
    if args.write_config:
        path = save_settings(settings, args.config or default_config_path())
        print(f"已写入配置：{path}")
        return 0

    enable_dpi_awareness()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(
            "无法创建图形界面。请确认当前会话有可用的桌面环境，"
            f"或在 Windows/macOS 上运行。\n{exc}",
            file=sys.stderr,
        )
        return 1

    root.title("屏幕白板")
    app = WhiteboardApp(root, settings)

    if settings.help_on_first_run and not args.no_help:
        root.after(350, lambda: _maybe_show_help(root, settings))

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
