# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""笔迹模型与高质量渲染。

所有坐标均为逻辑像素；渲染时按屏幕的 devicePixelRatio 放大到物理像素，
因此在 Retina / 高 DPI 屏幕上不会因缩放而发虚。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen

Point = Tuple[float, float]


@dataclass
class Stroke:
    points: List[Point] = field(default_factory=list)
    color: str = "#e53935"
    width: int = 3

    def append(self, x: float, y: float) -> None:
        self.points.append((float(x), float(y)))

    def last(self) -> Point:
        return self.points[-1]


def qcolor(value: str) -> QColor:
    color = QColor(value)
    return color if color.isValid() else QColor("#e53935")


def pen_for(stroke: Stroke) -> QPen:
    pen = QPen(qcolor(stroke.color), max(1.0, float(stroke.width)))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _mid(a: Point, b: Point) -> QPointF:
    return QPointF((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _qpoint(p: Point) -> QPointF:
    return QPointF(float(p[0]), float(p[1]))


def incremental_path(points: Sequence[Point]) -> Optional[QPainterPath]:
    """返回新增的一段平滑曲线（用于实时绘制）。

    points 是当前笔迹的全部点。新点到达时只绘制最后一小段，
    使用二次贝塞尔曲线连接相邻点的中点，得到丝滑的笔迹。
    """
    n = len(points)
    if n < 2:
        return None
    path = QPainterPath()
    if n == 2:
        path.moveTo(_qpoint(points[0]))
        path.lineTo(_mid(points[0], points[1]))
        return path
    start = _mid(points[-3], points[-2])
    end = _mid(points[-2], points[-1])
    path.moveTo(start)
    path.quadTo(_qpoint(points[-2]), end)
    return path


def tail_path(points: Sequence[Point]) -> Optional[QPainterPath]:
    """抬笔时补齐最后半段，避免笔迹在最后一个采样点前结束。"""
    if len(points) < 2:
        return None
    path = QPainterPath()
    path.moveTo(_mid(points[-2], points[-1]))
    path.lineTo(_qpoint(points[-1]))
    return path


def stroke_path(points: Sequence[Point]) -> QPainterPath:
    """完整的平滑笔迹路径（用于撤销后重绘）。"""
    path = QPainterPath()
    if not points:
        return path
    path.moveTo(_qpoint(points[0]))
    if len(points) == 1:
        return path
    for index in range(1, len(points)):
        if index == 1:
            path.lineTo(_mid(points[0], points[1]))
        else:
            start = _mid(points[index - 2], points[index - 1])
            end = _mid(points[index - 1], points[index])
            path.moveTo(start)
            path.quadTo(_qpoint(points[index - 1]), end)
    path.moveTo(_mid(points[-2], points[-1]))
    path.lineTo(_qpoint(points[-1]))
    return path


def draw_dot(painter: QPainter, point: Point, width: int, color: str) -> None:
    radius = max(0.5, width / 2.0)
    painter.setPen(Qt.NoPen)
    painter.setBrush(qcolor(color))
    painter.drawEllipse(_qpoint(point), radius, radius)


def draw_stroke(painter: QPainter, stroke: Stroke) -> None:
    if not stroke.points:
        return
    painter.setPen(pen_for(stroke))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(stroke_path(stroke.points))
    draw_dot(painter, stroke.points[0], stroke.width, stroke.color)


def stroke_bounds(points: Sequence[Point], width: int) -> QRectF:
    if not points:
        return QRectF()
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = width / 2.0 + 2.0
    return QRectF(
        min(xs) - pad, min(ys) - pad,
        max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad,
    )


def render_strokes(base: QImage, strokes: Iterable[Stroke]) -> QImage:
    """把笔迹绘制到截图的物理像素副本上，返回新图片。

    base 已通过 setDevicePixelRatio 记录缩放比例，QPainter 会自动把
    逻辑坐标映射到物理像素，因此这里不需要再手工缩放。
    """
    image = base.copy()
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    for stroke in strokes:
        draw_stroke(painter, stroke)
    painter.end()
    return image


def compose_ink(background: QImage, ink: QImage) -> QImage:
    """把透明笔迹层合成到背景图上，保持两者的物理像素一一对应。"""
    image = background.copy()
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, ink)
    painter.end()
    return image
