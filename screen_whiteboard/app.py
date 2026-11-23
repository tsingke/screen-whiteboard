# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""应用入口：悬浮按钮与标注层调度。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from . import __version__
from .capture import (
    ScreenCaptureError,
    grab_screen,
    open_screen_recording_settings,
    request_screen_capture_access,
    screen_capture_allowed,
)
from .config import (
    Settings,
    default_base_dir,
    default_config_path,
    load_settings,
    save_settings,
)
from .help import HelpDialog
from .launcher import Launcher
from .overlay import Overlay
from .platform_utils import configure_high_dpi, copy_settings, pick_font_family


class WhiteboardApp:
    """负责悬浮按钮、标注层生命周期与错误提示。"""

    def __init__(self, app: QApplication, settings: Settings) -> None:
        self.app = app
        self.settings = settings
        self.launcher = Launcher(settings)
        self.launcher.startRequested.connect(self.start_annotation)
        self.launcher.quitRequested.connect(self.app.quit)
        self.overlay: Optional[Overlay] = None
        self._pending = False

    # ------------------------------------------------------------------ 标注

    def start_annotation(self) -> None:
        if self._pending or self.overlay is not None:
            return
        if not screen_capture_allowed():
            self._show_permission_dialog()
            return
        self._pending = True
        self.launcher.hide()
        QTimer.singleShot(
            int(max(0.0, self.settings.hide_delay) * 1000),
            self._capture_and_show,
        )

    def _capture_and_show(self) -> None:
        try:
            screen = self.launcher.screen() or QGuiApplication.primaryScreen()
            if screen is None:
                raise ScreenCaptureError("没有检测到可用显示器。")
            capture = grab_screen(screen, all_monitors=self.settings.all_monitors)
            overlay = Overlay(capture, self.settings)
            overlay.closed.connect(self._on_overlay_closed)
            self.overlay = overlay

            geometry = screen.geometry()
            single_screen = (
                capture.origin_x == geometry.x()
                and capture.origin_y == geometry.y()
                and capture.width == geometry.width()
                and capture.height == geometry.height()
            )
            if sys.platform == "darwin" or not single_screen:
                # macOS 的原生全屏会保留 30px 菜单栏，这里用无边框窗口铺满整屏
                overlay.setGeometry(
                    capture.origin_x, capture.origin_y,
                    capture.width, capture.height,
                )
                overlay.show()
            else:
                # Windows / Linux 用原生全屏覆盖任务栏
                overlay.showFullScreen()
        except ScreenCaptureError as exc:
            QMessageBox.critical(None, "无法开始标注", str(exc))
            self._restore_launcher()
        except Exception as exc:  # 保证界面不会因单次异常退出
            QMessageBox.critical(None, "出错了", f"标注模式启动失败：\n{exc}")
            self._restore_launcher()
        finally:
            self._pending = False

    def _on_overlay_closed(self) -> None:
        self.overlay = None
        self._restore_launcher()

    def _restore_launcher(self) -> None:
        self.launcher.show()
        self.launcher.raise_()

    def _show_permission_dialog(self) -> None:
        box = QMessageBox(self.launcher)
        box.setWindowTitle("需要屏幕录制权限")
        box.setIcon(QMessageBox.Information)
        box.setText("macOS 需要「屏幕录制」权限，才能截取屏幕并进入标注模式。")
        box.setInformativeText(
            "请在「系统设置 → 隐私与安全性 → 屏幕录制」中勾选屏幕白板，"
            "然后完全退出并重新打开程序。"
        )
        open_button = box.addButton("打开系统设置", QMessageBox.ActionRole)
        box.addButton("稍后", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is open_button:
            request_screen_capture_access()
            open_screen_recording_settings()


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
        help="截取全部显示器（默认仅按钮所在屏幕）",
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


def _maybe_show_help(settings: Settings) -> None:
    if not settings.help_on_first_run:
        return
    marker = _first_run_marker()
    if marker.exists():
        return
    dialog = HelpDialog(settings)
    dialog.exec()
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("1\n", encoding="utf-8")
    except OSError:
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

    configure_high_dpi()
    app = QApplication([sys.argv[0]])
    app.setApplicationName("ScreenWhiteboard")
    app.setApplicationDisplayName("屏幕白板")
    app.setOrganizationName("tsingke")
    app.setStyle("Fusion")

    family = pick_font_family(settings.launcher_font_family)
    settings.launcher_font_family = family
    app.setFont(QFont(family, 10))

    controller = WhiteboardApp(app, settings)
    controller.launcher.show()

    if settings.help_on_first_run and not args.no_help:
        QTimer.singleShot(350, lambda: _maybe_show_help(settings))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
