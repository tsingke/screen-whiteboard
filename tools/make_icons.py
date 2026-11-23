#!/usr/bin/env python3
# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""生成应用图标与 README 界面示意图。

只在维护时运行；产物已提交到 assets/ 与 docs/。
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PNG_DIR = ASSETS / "png"
DOCS = ROOT / "docs"

PURPLE_TOP = (108, 76, 241)
PURPLE_BOTTOM = (155, 107, 255)


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (1, size))
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((size, size), Image.BILINEAR)


def draw_master(size: int = 2048) -> Image.Image:
    s = size
    scale = s / 1024.0
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    bg = gradient(s, PURPLE_TOP, PURPLE_BOTTOM).convert("RGBA")
    bg.putalpha(rounded_mask(s, int(230 * scale)))
    img.alpha_composite(bg)

    draw = ImageDraw.Draw(img)

    # 画板阴影
    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [int(170 * scale), int(250 * scale), int(858 * scale), int(816 * scale)],
        radius=int(44 * scale), fill=(30, 18, 76, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(22 * scale)))
    img.alpha_composite(shadow, (0, int(14 * scale)))

    # 白色画板
    draw.rounded_rectangle(
        [int(168 * scale), int(228 * scale), int(856 * scale), int(796 * scale)],
        radius=int(44 * scale), fill=(255, 255, 255, 255),
    )

    # 板上的彩色笔迹
    red = (229, 57, 53, 255)
    blue = (21, 101, 192, 255)
    green = (46, 125, 50, 255)
    yellow = (249, 168, 37, 255)

    draw.line(
        [(int(268 * scale), int(640 * scale)),
         (int(360 * scale), int(470 * scale)),
         (int(452 * scale), int(640 * scale)),
         (int(544 * scale), int(380 * scale))],
        fill=blue, width=int(34 * scale), joint="curve",
    )
    draw.line(
        [(int(300 * scale), int(720 * scale)), (int(720 * scale), int(720 * scale))],
        fill=red, width=int(30 * scale),
    )
    draw.line(
        [(int(600 * scale), int(318 * scale)),
         (int(700 * scale), int(318 * scale)),
         (int(700 * scale), int(418 * scale))],
        fill=green, width=int(30 * scale), joint="curve",
    )
    draw.ellipse(
        [int(610 * scale), int(520 * scale), int(700 * scale), int(610 * scale)],
        outline=yellow, width=int(28 * scale),
    )

    # 马克笔：斜放在画板右下角
    marker = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    md = ImageDraw.Draw(marker)
    body = [
        (int(700 * scale), int(820 * scale)),
        (int(790 * scale), int(730 * scale)),
        (int(868 * scale), int(808 * scale)),
        (int(778 * scale), int(898 * scale)),
    ]
    md.polygon(body, fill=(32, 33, 36, 255))
    md.polygon(
        [(int(790 * scale), int(730 * scale)), (int(820 * scale), int(700 * scale)),
         (int(898 * scale), int(778 * scale)), (int(868 * scale), int(808 * scale))],
        fill=(229, 57, 53, 255),
    )
    md.polygon(
        [(int(820 * scale), int(700 * scale)), (int(846 * scale), int(674 * scale)),
         (int(924 * scale), int(752 * scale)), (int(898 * scale), int(778 * scale))],
        fill=(250, 250, 250, 255),
    )
    tip = [
        (int(846 * scale), int(674 * scale)),
        (int(900 * scale), int(650 * scale)),
        (int(942 * scale), int(736 * scale)),
        (int(924 * scale), int(752 * scale)),
    ]
    md.polygon(tip, fill=(255, 193, 7, 255))
    img.alpha_composite(marker)

    return img


def save_icons(master: Image.Image) -> None:
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256, 512, 1024]
    for size in sizes:
        resized = master.resize((size, size), Image.LANCZOS)
        resized.save(PNG_DIR / f"screen-whiteboard-{size}.png")

    ico_sizes = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    master.resize((256, 256), Image.LANCZOS).save(
        ASSETS / "screen-whiteboard.ico",
        sizes=ico_sizes,
        format="ICO",
    )

    # macOS iconset
    iconset = ASSETS / "screen-whiteboard.iconset"
    if iconset.exists():
        for child in iconset.iterdir():
            child.unlink()
    iconset.mkdir(exist_ok=True)
    pairs = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    for size, name in pairs:
        master.resize((size, size), Image.LANCZOS).save(iconset / name)

    if sys.platform == "darwin":
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset),
             "-o", str(ASSETS / "screen-whiteboard.icns")],
            check=True,
        )


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


def make_preview() -> None:
    width, height = 1200, 675
    img = Image.new("RGB", (width, height), (238, 241, 247))
    draw = ImageDraw.Draw(img)

    # 桌面底色
    for y in range(height):
        t = y / height
        draw.line([(0, y), (width, y)],
                  fill=(int(236 - 10 * t), int(240 - 8 * t), int(248 - 6 * t)))

    # 教学画面（模拟一张课件）
    card = [70, 70, 1000, 605]
    draw.rounded_rectangle(card, radius=18, fill=(255, 255, 255), outline=(214, 220, 232), width=2)
    draw.rectangle([70, 70, 1000, 150], fill=(26, 115, 232))
    draw.text((100, 92), "二次函数 y = ax² + bx + c", font=load_font(34), fill=(255, 255, 255))

    # 坐标轴
    ox, oy = 300, 480
    draw.line([(150, oy), (930, oy)], fill=(120, 128, 145), width=2)
    draw.line([(ox, 190), (ox, 570)], fill=(120, 128, 145), width=2)
    for x in range(150, 931, 60):
        draw.line([(x, oy - 4), (x, oy + 4)], fill=(120, 128, 145), width=1)

    # 抛物线
    points = []
    for px in range(160, 920):
        nx = (px - ox) / 38.0
        y = 0.35 * nx * nx
        py = int(oy - 60 - y * 38)
        if 180 < py < 570:
            points.append((px, py))
    if len(points) > 1:
        draw.line(points, fill=(90, 110, 200), width=4)

    # 讲解标注（红蓝笔迹）
    draw.line([(420, 300), (520, 255), (640, 250)], fill=(229, 57, 53), width=6,
              joint="curve")
    draw.ellipse([540, 220, 730, 300], outline=(229, 57, 53), width=6)
    draw.line([(380, 540), (560, 500), (780, 520)], fill=(21, 101, 192), width=5,
              joint="curve")

    # 悬浮按钮
    button = [1030, 28, 1170, 78]
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([button[0] + 2, button[1] + 4, button[2] + 2, button[3] + 4],
                         radius=12, fill=(20, 40, 80, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(button, radius=12, fill=(26, 115, 232))
    draw.text((1053, 40), "开始手写", font=load_font(22), fill=(255, 255, 255))

    # 图注
    draw.text((72, 622), "界面示意图（实际为无边框悬浮按钮 + 全屏画布）",
              font=load_font(18), fill=(110, 118, 134))

    DOCS.mkdir(parents=True, exist_ok=True)
    img.save(DOCS / "ui-preview.png")


def main() -> None:
    master = draw_master()
    save_icons(master)
    make_preview()
    print("icons ->", ASSETS)
    print("preview ->", DOCS / "ui-preview.png")


if __name__ == "__main__":
    main()
