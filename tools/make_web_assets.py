#!/usr/bin/env python3
# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""生成官网所需的展示素材。

产物位于 docs/web/：主视觉、清晰度对比图、应用图标。
"""

from __future__ import annotations

import math
import pathlib
import shutil

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WEB = DOCS / "web"

BG = (246, 247, 251)
INK = (21, 21, 31)
MUTED = (94, 97, 114)
LINE = (228, 229, 239)
BRAND = (108, 76, 241)
BRAND_SOFT = (239, 234, 255)
PEN = (229, 72, 77)
BLUE = (21, 101, 192)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for path in candidates:
        if pathlib.Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_content(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """在 box 内画同一组内容，尺寸按高度等比例缩放。"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    unit = h / 100.0

    def px(fx: float, fy: float) -> tuple[float, float]:
        return x0 + w * fx, y0 + h * fy

    font = load_font(max(9, int(10 * unit)))
    draw.text(px(0.10, 0.12), "清晰书写", font=font, fill=INK)

    # 红色连笔曲线：一条略带起伏的手写线
    points = []
    for step in range(41):
        t = step / 40.0
        x = 0.10 + 0.78 * t
        y = 0.46 - 0.07 * math.sin(t * math.pi * 2.2) - 0.10 * t
        points.append(px(x, y))
    draw.line(points, fill=PEN, width=max(2, int(2.4 * unit)), joint="curve")
    radius = max(2, int(1.8 * unit))
    for x, y in (points[0], points[-1]):
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=PEN)

    # 蓝色圈注
    cx, cy = px(0.72, 0.74)
    radius = min(w, h) * 0.10
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=BLUE, width=max(2, int(2.6 * unit)),
    )

    # 绿色对勾
    draw.line(
        [px(0.14, 0.73), px(0.20, 0.80), px(0.31, 0.64)],
        fill=(15, 159, 110), width=max(2, int(2.6 * unit)), joint="curve",
    )


def make_compare() -> None:
    width, height = 1200, 560
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)

    label_font = load_font(21)
    caption_font = load_font(15)
    draw.text((40, 40), "普通位图放大 4×", font=label_font, fill=MUTED)
    draw.text((620, 40), "物理像素渲染 4×", font=label_font, fill=BRAND)

    panels = [(40, 84, 580, 496), (620, 84, 1160, 496)]
    for index, (x0, y0, x1, y1) in enumerate(panels):
        draw.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(255, 255, 255),
                               outline=LINE, width=1)
        inner_w, inner_h = (x1 - x0) - 24, (y1 - y0) - 24
        if index == 0:
            small = Image.new("RGB", (max(1, inner_w // 4), max(1, inner_h // 4)),
                              (255, 255, 255))
            draw_content(ImageDraw.Draw(small), (0, 0, small.width, small.height))
            upscaled = small.resize((inner_w, inner_h), Image.Resampling.BICUBIC)
            image.paste(upscaled, (x0 + 12, y0 + 12))
        else:
            layer = Image.new("RGB", (inner_w, inner_h), (255, 255, 255))
            draw_content(ImageDraw.Draw(layer), (0, 0, inner_w, inner_h))
            image.paste(layer, (x0 + 12, y0 + 12))

    draw.text(
        (40, 520),
        "示意图：同一画面在低分辨率放大与物理像素渲染下的差异",
        font=caption_font,
        fill=MUTED,
    )
    image.save(WEB / "crisp.png", optimize=True)


def main() -> None:
    WEB.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DOCS / "ui-preview.png", WEB / "hero.png")
    shutil.copyfile(ROOT / "assets" / "png" / "screen-whiteboard-256.png",
                    WEB / "icon-256.png")
    make_compare()
    print("web assets ->", WEB)


if __name__ == "__main__":
    main()
