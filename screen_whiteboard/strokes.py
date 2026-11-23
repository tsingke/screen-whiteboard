# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""笔迹模型与离屏渲染。

保存截图时把笔迹重绘到原始截图上，而不是重新抓屏，这样：
1. 不会把白板窗口本身拍进图片；
2. 不会把保存前弹出的其他窗口拍进去；
3. 渲染过程可单元测试。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageColor, ImageDraw

Point = Tuple[int, int]


@dataclass
class Stroke:
    points: List[Point] = field(default_factory=list)
    color: str = "#e53935"
    width: int = 3
    tag: str = ""

    def append(self, x: int, y: int) -> None:
        self.points.append((int(x), int(y)))


def rgb(color: str) -> Tuple[int, int, int]:
    """把 Tk/PIL 支持的任意颜色写法转成 RGB 三元组。"""
    try:
        value = ImageColor.getrgb(color)
    except ValueError:
        value = ImageColor.getrgb("#e53935")
    if len(value) == 4:
        value = value[:3]
    return value  # type: ignore[return-value]


def _draw_cap(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float,
              color: Tuple[int, int, int]) -> None:
    if radius <= 0:
        return
    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        fill=color,
    )


def render_strokes(
    base: Image.Image,
    strokes: Iterable[Stroke],
    scale: float = 1.0,
) -> Image.Image:
    """返回一张新图片：base 的副本 + 所有笔迹。"""
    image = base.convert("RGB").copy()
    draw = ImageDraw.Draw(image)
    ratio = float(scale) if scale else 1.0

    for stroke in strokes:
        if not stroke.points:
            continue
        color = rgb(stroke.color)
        width = max(1, int(round(max(1, stroke.width) * ratio)))
        points: Sequence[Point] = [
            (int(round(x * ratio)), int(round(y * ratio))) for x, y in stroke.points
        ]
        if len(points) == 1:
            _draw_cap(draw, points[0][0], points[0][1], width / 2.0, color)
            continue
        draw.line(points, fill=color, width=width, joint="curve")
        # freehand 线段的端点用圆头补齐，效果与 Tk 的 capstyle=round 一致
        radius = width / 2.0
        _draw_cap(draw, points[0][0], points[0][1], radius, color)
        _draw_cap(draw, points[-1][0], points[-1][1], radius, color)

    return image
