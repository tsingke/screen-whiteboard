# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""全屏标注层。"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Optional

from PIL import ImageTk

from .capture import Capture
from .config import Settings
from .keymap import ActionType, resolve_key
from .strokes import Stroke, render_strokes

COLOR_NAMES = {
    "r": "红",
    "g": "绿",
    "b": "蓝",
    "y": "黄",
    "k": "黑",
    "w": "白",
}


class AnnotationOverlay:
    """覆盖在冻结画面之上的画布。

    使用 overrideredirect 的无边框窗口，铺满被截屏的区域。
    """

    def __init__(self, master: tk.Misc, capture: Capture, settings: Settings) -> None:
        self.master = master
        self.capture = capture
        self.settings = settings

        self.color = settings.colors[settings.default_color]
        self.width = settings.default_width

        self.strokes: list[Stroke] = []
        self._stroke: Optional[Stroke] = None
        self._stroke_tag: Optional[str] = None
        self._counter = 0
        self._hud_job: Optional[str] = None

        self.top = tk.Toplevel(master)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.geometry(
            f"{capture.width}x{capture.height}"
            f"+{capture.origin_x}+{capture.origin_y}"
        )
        self.top.configure(bg="white")

        self.canvas = tk.Canvas(
            self.top,
            width=capture.width,
            height=capture.height,
            bg="white",
            highlightthickness=0,
            bd=0,
            cursor=settings.cursor,
        )
        self.canvas.pack(fill="both", expand=True)

        self.photo = ImageTk.PhotoImage(capture.image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo, tags=("background",))

        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Key>", self._on_key)
        self.canvas.bind("<Escape>", lambda _event: self.close())

        self.top.bind("<Key>", self._on_key)
        self.top.bind("<Escape>", lambda _event: self.close())

        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.update_idletasks()
        self.top.focus_force()
        self.canvas.focus_force()
        try:
            self.top.grab_set()
        except tk.TclError:
            # 某些窗口管理器不允许抢占输入，不影响键盘绑定。
            pass

    # ------------------------------------------------------------------ 绘制

    def _on_press(self, event: tk.Event) -> None:
        self._counter += 1
        tag = f"stroke-{self._counter}"
        self._stroke = Stroke(points=[], color=self.color, width=self.width, tag=tag)
        self._stroke_tag = tag
        self.strokes.append(self._stroke)
        self._stroke.append(event.x, event.y)
        radius = max(1, self.width / 2.0)
        self.canvas.create_oval(
            event.x - radius, event.y - radius,
            event.x + radius, event.y + radius,
            fill=self.color, outline=self.color, tags=(tag, "ink"),
        )

    def _on_drag(self, event: tk.Event) -> None:
        if self._stroke is None:
            self._on_press(event)
            return
        previous = self._stroke.points[-1]
        self._stroke.append(event.x, event.y)
        self.canvas.create_line(
            previous[0], previous[1], event.x, event.y,
            fill=self._stroke.color,
            width=max(1, self._stroke.width),
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=False,
            tags=(self._stroke_tag, "ink"),
        )

    def _on_release(self, _event: tk.Event) -> None:
        self._stroke = None
        self._stroke_tag = None

    # ------------------------------------------------------------------ 键盘

    def _on_key(self, event: tk.Event) -> str:
        # ControlMask = 0x4；macOS 上 Command 走 Mod1 = 0x8
        ctrl = bool(event.state & 0x4 or event.state & 0x8)
        action = resolve_key(event.char, event.keysym, ctrl=ctrl, colors=self.settings.colors)
        if action.type is ActionType.COLOR:
            self.color = str(action.value)
            self._show_hud()
        elif action.type is ActionType.WIDTH:
            self.width = int(action.value)
            self._show_hud()
        elif action.type is ActionType.CLEAR:
            self.clear()
        elif action.type is ActionType.SAVE:
            self.save()
        elif action.type is ActionType.UNDO:
            self.undo()
        elif action.type is ActionType.CLOSE:
            self.close()
        return "break"

    def _show_hud(self) -> None:
        name = "自定义"
        for key, value in self.settings.colors.items():
            if value.lower() == self.color.lower():
                name = COLOR_NAMES.get(key, key)
                break
        self.canvas.delete("hud")
        text_id = self.canvas.create_text(
            36, 32, anchor="nw",
            text=f"颜色：{name}    线宽：{self.width}",
            fill="#ffffff",
            font=(self.settings.launcher_font_family, 14, "bold"),
            tags=("hud",),
        )
        box = self.canvas.bbox(text_id)
        if box:
            rect = self.canvas.create_rectangle(
                box[0] - 12, box[1] - 8, box[2] + 12, box[3] + 8,
                fill="#202124", outline="", tags=("hud",),
            )
            self.canvas.tag_lower(rect, text_id)
        if self._hud_job is not None:
            self.top.after_cancel(self._hud_job)
        self._hud_job = self.top.after(1200, lambda: self.canvas.delete("hud"))

    # ------------------------------------------------------------------ 动作

    def clear(self) -> None:
        """只清除笔迹，保留作为背景的屏幕画面。"""
        self.canvas.delete("ink")
        self.strokes.clear()
        self._stroke = None
        self._stroke_tag = None

    def undo(self) -> None:
        if not self.strokes:
            return
        stroke = self.strokes.pop()
        if stroke.tag:
            self.canvas.delete(stroke.tag)
        self._stroke = None
        self._stroke_tag = None

    def save(self) -> None:
        default_name = f"白板_{datetime.now():%Y%m%d_%H%M%S}.png"
        path = filedialog.asksaveasfilename(
            parent=self.top,
            title="保存截图",
            initialfile=default_name,
            initialdir=str(self.settings.resolved_save_dir()),
            defaultextension=".png",
            filetypes=[
                ("PNG 图片", "*.png"),
                ("JPEG 图片", "*.jpg *.jpeg"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return

        target = Path(path)
        if target.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            target = target.with_suffix(".png")

        scale = self.capture.image.width / max(1, self.capture.width)
        image = render_strokes(self.capture.image, self.strokes, scale=scale)
        try:
            if target.suffix.lower() in (".jpg", ".jpeg"):
                image.save(target, quality=95, optimize=True)
            else:
                image.save(target, optimize=True)
        except OSError as exc:
            from tkinter import messagebox

            messagebox.showerror("保存失败", f"无法写入文件：\n{exc}", parent=self.top)
            return
        self.close()

    def close(self) -> None:
        if self._hud_job is not None:
            try:
                self.top.after_cancel(self._hud_job)
            except tk.TclError:
                pass
            self._hud_job = None
        try:
            self.top.grab_release()
        except tk.TclError:
            pass
        try:
            self.top.destroy()
        except tk.TclError:
            pass

    def wait(self) -> None:
        self.top.wait_window()
