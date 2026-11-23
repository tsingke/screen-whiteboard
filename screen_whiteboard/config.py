# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""配置模型与读写。

所有字段都有安全默认值；项目不会在未授权的情况下修改系统设置。
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

APP_NAME = "ScreenWhiteboard"

DEFAULT_COLORS: Dict[str, str] = {
    "r": "#e53935",  # 红
    "g": "#2e7d32",  # 绿
    "b": "#1565c0",  # 蓝
    "y": "#f9a825",  # 黄
    "k": "#212121",  # 黑
    "w": "#ffffff",  # 白
}


def default_font_family() -> str:
    """按平台挑选一个常见的中文界面字体。"""
    if sys.platform == "win32":
        return "Microsoft YaHei UI"
    if sys.platform == "darwin":
        return "PingFang SC"
    return "Noto Sans CJK SC"


def default_base_dir() -> Path:
    """返回跨平台的配置目录（不主动创建）。"""
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or str(Path.home())
        return Path(root) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    root = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(root) / "screen-whiteboard"


def default_config_path() -> Path:
    return default_base_dir() / "config.json"


def default_save_dir() -> Path:
    """默认保存到系统图片目录，取不到时退回当前目录。"""
    pictures = Path.home() / "Pictures"
    if pictures.is_dir():
        return pictures
    return Path.cwd()


@dataclass
class Settings:
    """可序列化的运行配置。"""

    colors: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLORS))
    default_color: str = "r"
    default_width: int = 3
    min_width: int = 1
    max_width: int = 9

    launcher_text: str = "开始手写"
    launcher_bg: str = "#6c4cf1"
    launcher_bg_bottom: str = "#9b6bff"
    launcher_fg: str = "#ffffff"
    launcher_active_bg: str = "#5b3fe6"
    launcher_font_family: str = field(default_factory=default_font_family)
    launcher_font_size: int = 13
    launcher_padx: int = 20
    launcher_pady: int = 10
    launcher_radius: int = 16
    launcher_shadow: bool = True

    offset_x: int = 20
    offset_y: int = 10
    hide_delay: float = 0.15

    save_dir: str = ""
    all_monitors: bool = False
    help_on_first_run: bool = True

    def resolved_save_dir(self) -> Path:
        if self.save_dir:
            path = Path(self.save_dir).expanduser()
            if path.is_dir():
                return path
        return default_save_dir()

    def validate(self) -> None:
        """把明显越界的值钳制回合理范围，避免界面异常。"""
        self.min_width = max(1, int(self.min_width))
        self.max_width = max(self.min_width, int(self.max_width))
        self.default_width = max(self.min_width, min(self.max_width, int(self.default_width)))
        self.hide_delay = max(0.0, min(3.0, float(self.hide_delay)))
        self.offset_x = max(0, int(self.offset_x))
        self.offset_y = max(0, int(self.offset_y))
        self.launcher_font_size = max(8, min(36, int(self.launcher_font_size)))
        self.launcher_padx = max(4, min(80, int(self.launcher_padx)))
        self.launcher_pady = max(2, min(60, int(self.launcher_pady)))
        self.launcher_radius = max(0, min(40, int(self.launcher_radius)))
        if self.default_color not in self.colors:
            self.default_color = next(iter(self.colors))


def _coerce_settings(raw: Dict[str, Any], base: Optional[Settings] = None) -> Settings:
    """把 JSON 字典合并到默认配置上，忽略未知字段与类型不符的值。"""
    settings = base or Settings()
    known = {f for f in asdict(settings)}
    for key, value in raw.items():
        if key not in known:
            continue
        current = getattr(settings, key)
        try:
            if key == "colors":
                if isinstance(value, dict):
                    colors = {str(k): str(v) for k, v in value.items() if isinstance(v, str)}
                    if colors:
                        settings.colors = colors
            elif isinstance(current, bool):
                if isinstance(value, bool):
                    setattr(settings, key, value)
            elif isinstance(current, int):
                setattr(settings, key, int(value))
            elif isinstance(current, float):
                setattr(settings, key, float(value))
            elif isinstance(current, str):
                setattr(settings, key, str(value))
        except (TypeError, ValueError):
            continue
    settings.validate()
    return settings


def load_settings(path: Optional[Path] = None) -> Settings:
    """读取配置文件；文件不存在或损坏时返回默认配置。"""
    path = Path(path) if path else default_config_path()
    if not path.is_file():
        return Settings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    return _coerce_settings(raw)


def save_settings(settings: Settings, path: Optional[Path] = None) -> Path:
    """把配置写入 JSON，返回实际路径。"""
    path = Path(path) if path else default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
