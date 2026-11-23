# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""应用内使用说明窗口。"""

from __future__ import annotations

import tkinter as tk

from .config import Settings

HELP_TEXT = """\
【开始标注】

点击右上角的「开始手写」按钮，屏幕画面会冻结并被覆盖，
此时可以用鼠标左键自由书写、画线。

【退出程序】

在「开始手写」按钮上单击鼠标右键。
按钮可以用左键拖动到屏幕上的任意位置。

【标注模式中的快捷键】

R / G / B        切换红、绿、蓝
Y / K / W        切换黄、黑、白
1 ~ 9            切换线条粗细
C                清除全部笔迹
Ctrl + Z         撤销上一笔
S 或 Ctrl + S    保存截图（PNG / JPEG）
Esc              退出标注模式

【小提示】

· 标注模式会截取当前主屏幕，动手前请先准备好要讲的内容。
· macOS 首次使用需要在「系统设置 → 隐私与安全性 → 屏幕录制」中授权。
· Windows 可在启动参数中使用 --all-monitors 覆盖全部显示器。
"""


class HelpWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, settings: Settings) -> None:
        super().__init__(master)
        self.title("使用说明 · 屏幕白板")
        self.configure(bg="#f7f8fa")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        header = tk.Label(
            self,
            text="屏幕白板 · 使用说明",
            bg="#1a73e8",
            fg="#ffffff",
            font=(settings.launcher_font_family, 16, "bold"),
            anchor="w",
            padx=20,
            pady=14,
        )
        header.pack(fill="x")

        body = tk.Text(
            self,
            width=56,
            height=20,
            bg="#ffffff",
            fg="#202124",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=16,
            font=(settings.launcher_font_family, 11),
            wrap="word",
        )
        body.insert("1.0", HELP_TEXT)
        body.configure(state="disabled")
        body.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        footer = tk.Frame(self, bg="#f7f8fa")
        footer.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(
            footer,
            text="知道了",
            command=self.destroy,
            bg="#1a73e8",
            fg="#ffffff",
            activebackground="#1557b0",
            activeforeground="#ffffff",
            relief="flat",
            padx=22,
            pady=6,
            font=(settings.launcher_font_family, 11, "bold"),
            cursor="hand2",
        ).pack(side="right")

        self.bind("<Escape>", lambda _event: self.destroy())
        self.update_idletasks()
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 3)
        self.geometry(f"+{x}+{y}")
