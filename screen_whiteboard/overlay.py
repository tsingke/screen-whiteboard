# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""全屏标注层：原生 HiDPI 渲染 + 增量绘制。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
)
from PySide6.QtWidgets import QFileDialog, QWidget

from .capture import Capture
from .config import Settings
from .keymap import ActionType, resolve_key
from .strokes import (
    Stroke,
    compose_ink,
    draw_dot,
    draw_stroke,
    incremental_path,
    pen_for,
    stroke_bounds,
    tail_path,
)

COLOR_NAMES = {
    "r": "红",
    "g": "绿",
    "b": "蓝",
    "y": "黄",
    "k": "黑",
    "w": "白",
}


class Overlay(QWidget):
    """覆盖在冻结画面上的无边框画布。"""

    closed = Signal()

    def __init__(self, capture: Capture, settings: Settings) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window,
        )
        self.capture = capture
        self.settings = settings

        self.color = settings.colors[settings.default_color]
        self.width = settings.default_width
        self.strokes: List[Stroke] = []
        self.current: Optional[Stroke] = None

        self._ink_painter: Optional[QPainter] = None
        self._closed = False
        self._shown_once = False
        self._hud_text = ""
        self._hud_visible = False
        self._hud_rect = QRect()

        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setGeometry(
            capture.origin_x, capture.origin_y, capture.width, capture.height
        )

        self.ink = QImage(
            capture.image.size(), QImage.Format_ARGB32_Premultiplied
        )
        self.ink.fill(Qt.transparent)
        self.ink.setDevicePixelRatio(capture.dpr)

        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.timeout.connect(self._hide_hud)

        self._font = QFont(settings.launcher_font_family, 12)
        self._font.setBold(True)

    # ------------------------------------------------------------------ 绘制

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawImage(0, 0, self.capture.image)
        painter.drawImage(0, 0, self.ink)
        self._draw_hud(painter)
        painter.end()

    def _status_text(self) -> str:
        name = "自定义"
        for key, value in self.settings.colors.items():
            if value.lower() == self.color.lower():
                name = COLOR_NAMES.get(key, key)
                break
        return f"颜色：{name}    线宽：{self.width}"

    def _hud_geometry(self) -> QRect:
        metrics = QFontMetrics(self._font)
        text = self._hud_text or self._status_text()
        width = metrics.horizontalAdvance(text) + 28
        height = metrics.height() + 16
        return QRect(20, 20, width, height)

    def _draw_hud(self, painter: QPainter) -> None:
        if not self._hud_visible:
            return
        rect = self._hud_rect
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(22, 24, 32, 225))
        painter.drawRoundedRect(QRectF(rect), 10, 10)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(self._font)
        painter.drawText(QRectF(rect), Qt.AlignCenter, self._hud_text)

    def _show_hud_once(self, text: str) -> None:
        self._hud_text = text
        self._hud_rect = self._hud_geometry().adjusted(-4, -4, 4, 4)
        self._hud_visible = True
        self._hud_timer.start(1300)
        self.update(self._hud_rect)

    def _hide_hud(self) -> None:
        self._hud_visible = False
        self.update(self._hud_rect)

    # ------------------------------------------------------------------ 笔迹

    def _begin_ink(self) -> None:
        if self._ink_painter is not None:
            return
        self._ink_painter = QPainter(self.ink)
        self._ink_painter.setRenderHint(QPainter.Antialiasing, True)

    def _end_ink(self) -> None:
        if self._ink_painter is not None:
            self._ink_painter.end()
            self._ink_painter = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            event.accept()
            return
        point = (event.position().x(), event.position().y())
        self.current = Stroke(points=[point], color=self.color, width=self.width)
        self.strokes.append(self.current)
        self._begin_ink()
        assert self._ink_painter is not None
        draw_dot(self._ink_painter, point, self.width, self.color)
        rect = stroke_bounds([point], self.width).toAlignedRect()
        self.update(rect)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.current is None or not (event.buttons() & Qt.LeftButton):
            event.accept()
            return
        position = event.position()
        previous = self.current.last()
        if abs(position.x() - previous[0]) < 0.4 and abs(position.y() - previous[1]) < 0.4:
            event.accept()
            return

        self.current.append(position.x(), position.y())
        assert self._ink_painter is not None
        self._ink_painter.setPen(pen_for(self.current))
        self._ink_painter.setBrush(Qt.NoBrush)
        path = incremental_path(self.current.points)
        if path is not None:
            self._ink_painter.drawPath(path)
        rect = stroke_bounds(self.current.points[-4:], self.width).toAlignedRect()
        self.update(rect)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.current is not None:
            assert self._ink_painter is not None
            path = tail_path(self.current.points)
            if path is not None:
                self._ink_painter.setPen(pen_for(self.current))
                self._ink_painter.setBrush(Qt.NoBrush)
                self._ink_painter.drawPath(path)
                self.update(stroke_bounds(self.current.points[-2:], self.width).toAlignedRect())
            self._end_ink()
            self.current = None
        event.accept()

    # ------------------------------------------------------------------ 操作

    def clear(self) -> None:
        self._end_ink()
        self.strokes.clear()
        self.current = None
        self.ink.fill(Qt.transparent)
        self.update()

    def undo(self) -> None:
        if not self.strokes:
            return
        self._end_ink()
        self.strokes.pop()
        self.current = None
        self._repaint_ink()
        self.update()

    def _repaint_ink(self) -> None:
        self.ink.fill(Qt.transparent)
        painter = QPainter(self.ink)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for stroke in self.strokes:
            draw_stroke(painter, stroke)
        painter.end()

    def save(self) -> None:
        self._end_ink()
        default_name = f"白板_{datetime.now():%Y%m%d_%H%M%S}.png"
        start = self.settings.resolved_save_dir() / default_name
        path, selected = QFileDialog.getSaveFileName(
            self,
            "保存截图",
            str(start),
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg *.jpeg)",
        )
        if not path:
            return

        target = Path(path)
        if target.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            target = target.with_suffix(".jpg" if "JPEG" in selected else ".png")

        image = compose_ink(self.capture.image, self.ink)

        fmt = "JPEG" if target.suffix.lower() in (".jpg", ".jpeg") else "PNG"
        ok = image.save(str(target), fmt, 95 if fmt == "JPEG" else -1)
        if not ok:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "保存失败", f"无法写入文件：\n{target}")
            return
        self.close()

    # ------------------------------------------------------------------ 键盘

    def keyPressEvent(self, event: QKeyEvent) -> None:
        ctrl = bool(event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier))
        if event.key() == Qt.Key_Escape:
            action = resolve_key("", "Escape", colors=self.settings.colors)
        elif ctrl and event.key() == Qt.Key_Z:
            action = resolve_key("z", "z", ctrl=True, colors=self.settings.colors)
        elif ctrl and event.key() == Qt.Key_S:
            action = resolve_key("s", "s", ctrl=True, colors=self.settings.colors)
        else:
            text = event.text()
            action = resolve_key(text, text, colors=self.settings.colors)

        if action.type is ActionType.COLOR:
            self.color = str(action.value)
            self._show_hud_once(self._status_text())
        elif action.type is ActionType.WIDTH:
            self.width = int(action.value)
            self._show_hud_once(self._status_text())
        elif action.type is ActionType.CLEAR:
            self.clear()
            self._show_hud_once("已清空")
        elif action.type is ActionType.SAVE:
            self.save()
        elif action.type is ActionType.UNDO:
            self.undo()
            self._show_hud_once("已撤销")
        elif action.type is ActionType.CLOSE:
            self.close()
        event.accept()

    # ------------------------------------------------------------------ 生命周期

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.OtherFocusReason)
        if not self._shown_once:
            self._shown_once = True
            self._show_hud_once(self._status_text())

    def closeEvent(self, event) -> None:
        self._end_ink()
        if not self._closed:
            self._closed = True
            self.closed.emit()
        super().closeEvent(event)
