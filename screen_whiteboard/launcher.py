# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""圆角渐变悬浮按钮。"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget

from .config import Settings

SHADOW = 10


class Launcher(QWidget):
    """始终置顶的小按钮：左键单击开始标注，按住可拖动，右键退出。"""

    startRequested = Signal()
    quitRequested = Signal()

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint,
        )
        self.settings = settings
        self._hover = False
        self._pressed = False
        self._drag_offset: QPoint | None = None
        self._moved = False

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("左键：开始手写并标注\n拖动：移动按钮\n右键：退出程序")

        self._font = QFont(settings.launcher_font_family, settings.launcher_font_size)
        self._font.setBold(True)
        metrics = QFontMetrics(self._font)
        width = metrics.horizontalAdvance(settings.launcher_text) + settings.launcher_padx * 2
        height = metrics.height() + settings.launcher_pady * 2
        self.setFixedSize(width + SHADOW * 2, height + SHADOW * 2)
        self._content_height = height
        self.place_top_right()

    def place_top_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        x = area.right() + 1 - self.width() + SHADOW - self.settings.offset_x
        y = area.top() + self.settings.offset_y - SHADOW
        self.move(x, y)

    # ------------------------------------------------------------------ 绘制

    def _content_rect(self) -> QRectF:
        return QRectF(
            SHADOW, SHADOW,
            self.width() - SHADOW * 2,
            self.height() - SHADOW * 2,
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        content = self._content_rect()
        radius = float(self.settings.launcher_radius)

        if self.settings.launcher_shadow:
            for spread in range(SHADOW, 0, -1):
                alpha = int(2 + 4 * (1 - spread / float(SHADOW)))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(24, 20, 60, alpha))
                painter.drawRoundedRect(
                    content.adjusted(-spread, -spread + 2, spread, spread),
                    radius + spread,
                    radius + spread,
                )

        top = QColor(self.settings.launcher_bg)
        bottom = QColor(self.settings.launcher_bg_bottom)
        if self._pressed:
            top = QColor(self.settings.launcher_active_bg)
            bottom = top.darker(110)
        elif self._hover:
            top = top.lighter(112)
            bottom = bottom.lighter(106)

        gradient = QLinearGradient(content.topLeft(), content.bottomLeft())
        gradient.setColorAt(0.0, top)
        gradient.setColorAt(1.0, bottom)
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(content, radius, radius)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 46), 1))
        painter.drawRoundedRect(content.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        painter.setPen(QColor(self.settings.launcher_fg))
        painter.setFont(self._font)
        painter.drawText(content, Qt.AlignCenter, self.settings.launcher_text)
        painter.end()

    # ------------------------------------------------------------------ 交互

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._moved = False
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.update()
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.quitRequested.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pressed and self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            target = event.globalPosition().toPoint() - self._drag_offset
            if (target - self.pos()).manhattanLength() > 2:
                self._moved = True
            self.move(self._clamp(target))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self._drag_offset = None
            self.update()
            if not self._moved:
                self.startRequested.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _clamp(self, point: QPoint) -> QPoint:
        screens = QGuiApplication.screens()
        if not screens:
            return point
        area = screens[0].geometry()
        for screen in screens[1:]:
            area = area.united(screen.geometry())
        x = max(area.left(), min(point.x(), area.right() + 1 - self.width()))
        y = max(area.top(), min(point.y(), area.bottom() + 1 - self.height()))
        return QPoint(x, y)
