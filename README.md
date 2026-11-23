# 屏幕白板 · Screen Whiteboard

一个开源、跨平台的屏幕白板教学工具：屏幕右上角悬浮一个「开始手写」按钮，点击后冻结当前画面，直接用鼠标在屏幕上书写、圈画，并按需保存截图。

项目源于对一款 Windows 教学白板软件的逆向分析，随后以干净房间方式重新实现。只借鉴功能与交互，不包含原软件的任何代码、图片或文本资源。

[![build](https://github.com/tsingke/screen-whiteboard/actions/workflows/build.yml/badge.svg)](https://github.com/tsingke/screen-whiteboard/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776ab.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6b7280.svg)](#平台说明)

![界面示意图](docs/ui-preview.png)

> 上图为界面示意图，用于说明交互方式；实际界面为无边框悬浮按钮 + 全屏冻结画布。

## 功能

| 功能 | 说明 |
|---|---|
| 悬浮入口 | 无边框、始终置顶的「开始手写」按钮，默认位于右上角 |
| 自由拖动 | 左键按住按钮即可拖到任意位置 |
| 快速退出 | 在按钮上单击右键退出程序（macOS 支持右键或双指点按） |
| 冻结标注 | 点击后截取当前主屏，在冻结画面上书写，不干扰底层窗口 |
| 颜色切换 | 红 / 绿 / 蓝 / 黄 / 黑 / 白 |
| 线宽切换 | 1 ~ 9 级 |
| 撤销 | Ctrl+Z 撤销上一笔 |
| 清空 | C 键清空全部笔迹，保留屏幕背景 |
| 截图保存 | S 键保存为 PNG / JPEG，默认文件名带时间戳 |
| 高 DPI | Windows 启动时启用 Per-Monitor V2 DPI 感知 |
| 多显示器 | Windows 下可用 `--all-monitors` 截取整个虚拟桌面 |
| 无外部服务 | 不联网、不写注册表、不上传任何内容 |

## 快速开始

### 从源码运行

```bash
git clone https://github.com/tsingke/screen-whiteboard.git
cd screen-whiteboard
python -m pip install -r requirements.txt
python main.py
```

也可以安装为命令：

```bash
python -m pip install .
screen-whiteboard
```

### 使用预构建版本

在 [Releases](https://github.com/tsingke/screen-whiteboard/releases) 下载：

| 下载文件 | 内容 |
|---|---|
| `ScreenWhiteboard-v1.0.2-Windows-macOS.zip` | 双平台合集，内含 `Windows版/` 与 `macOS版/` 两个独立文件夹 |
| `ScreenWhiteboard-Windows.exe` | Windows 单文件版 |
| `ScreenWhiteboard-macOS.dmg` | macOS 安装镜像 |
| `ScreenWhiteboard-macOS.zip` | macOS App 压缩包 |

合集解压后的结构：

```text
ScreenWhiteboard-v1.0.2-Windows-macOS/
├── Windows版/
│   ├── ScreenWhiteboard.exe
│   ├── 使用说明.txt
│   └── LICENSE.txt
└── macOS版/
    ├── ScreenWhiteboard-macOS.dmg
    ├── ScreenWhiteboard-macOS.zip
    ├── 使用说明.txt
    └── LICENSE.txt
```

Windows 直接双击 `ScreenWhiteboard.exe` 运行。macOS 打开 DMG，把 `ScreenWhiteboard.app` 拖到「应用程序」；首次启动请右键点击 App 选择「打开」，并在「系统设置 → 隐私与安全性 → 屏幕录制」中授权。

## 快捷键

| 按键 | 作用 |
|---|---|
| 鼠标左键拖动 | 书写 / 画线 |
| R / G / B | 红色 / 绿色 / 蓝色 |
| Y / K / W | 黄色 / 黑色 / 白色 |
| 1 ~ 9 | 线条粗细 |
| C | 清空笔迹 |
| Ctrl+Z | 撤销上一笔 |
| S 或 Ctrl+S | 保存截图 |
| Esc | 退出标注模式 |

标注模式下左上角会短暂显示当前颜色与线宽。

## 命令行参数

```text
python main.py [--config PATH] [--offset-x N] [--offset-y N]
               [--save-dir DIR] [--all-monitors] [--no-help]
               [--print-config] [--write-config]
```

| 参数 | 说明 |
|---|---|
| `--config PATH` | 指定 JSON 配置文件 |
| `--offset-x N` | 按钮距离屏幕右侧的像素，默认 20 |
| `--offset-y N` | 按钮距离屏幕顶部的像素，默认 10 |
| `--save-dir DIR` | 截图默认保存目录 |
| `--all-monitors` | Windows 下截取全部显示器 |
| `--no-help` | 首次启动时不显示使用说明 |
| `--print-config` | 打印生效配置后退出 |
| `--write-config` | 将配置写入默认位置后退出 |

配置文件位置：

| 平台 | 路径 |
|---|---|
| Windows | `%APPDATA%\ScreenWhiteboard\config.json` |
| macOS | `~/Library/Application Support/ScreenWhiteboard/config.json` |
| Linux | `~/.config/screen-whiteboard/config.json` |

所有字段都有默认值，配置文件不是必需的。可配置项包括颜色表、默认颜色与线宽、按钮文字与配色、偏移、字体、保存目录等，详见 `screen_whiteboard/config.py`。

## 打包

Windows：

```bat
build\build_windows.bat
```

macOS：

```bash
bash build/build_macos.sh
```

产物位于 `dist/`。CI 也会在每次推送到 `main` 或打 `v*` 标签时自动构建两个平台的安装包。

## 平台说明

| 平台 | 截屏方式 | 注意事项 |
|---|---|---|
| Windows | Pillow `ImageGrab` | 首次运行若被 SmartScreen 拦截，选择「更多信息 → 仍要运行」 |
| macOS | `screencapture` | 须在「系统设置 → 隐私与安全性 → 屏幕录制」中给终端或 App 授权 |
| Linux | ImageGrab / gnome-screenshot / spectacle / scrot / grim / ImageMagick | 安装其中任意一种截图工具即可；Wayland 下建议用 grim |

macOS 的 Retina 屏幕截图是物理像素，程序会自动缩放到 Tk 的逻辑坐标，保证笔迹与画面严格对齐。

Release 中的 macOS 构建为 Apple Silicon（arm64）。Intel Mac 可以从源码运行，或执行 `bash build/build_macos.sh` 自行打包。

## 项目结构

```text
screen-whiteboard/
├── main.py                        # 入口
├── screen_whiteboard/
│   ├── app.py                     # 悬浮按钮、调度标注层
│   ├── overlay.py                 # 全屏画布、快捷键、保存
│   ├── strokes.py                 # 笔迹模型与离屏渲染
│   ├── capture.py                 # 跨平台截屏
│   ├── keymap.py                  # 按键 → 动作（纯函数）
│   ├── config.py                  # 配置模型与读写
│   ├── help.py                    # 应用内使用说明
│   └── platform_utils.py          # DPI、屏幕尺寸
├── tools/
│   ├── nuitka_onefile_extract.py  # Nuitka onefile 提取工具
│   └── make_icons.py              # 图标与示意图生成
├── tests/                         # 单元测试
├── docs/
│   ├── reverse-engineering.md     # 原始软件逆向分析报告
│   └── ui-preview.png
├── assets/                        # ICO / ICNS / PNG
├── build/                         # 打包脚本
└── .github/workflows/build.yml    # 测试 + 双平台构建 + Release
```

## 逆向分析

对原始 Windows 软件的分析过程、文件格式、恢复出的交互细节，以及提取工具的用法，见：

- [docs/reverse-engineering.md](docs/reverse-engineering.md)
- [tools/nuitka_onefile_extract.py](tools/nuitka_onefile_extract.py)

提取工具可独立使用：

```bash
python -m pip install zstandard
python tools/nuitka_onefile_extract.py 目标程序.exe --list
python tools/nuitka_onefile_extract.py 目标程序.exe -o 输出目录
```

它只做字节级解析，不执行被提取的文件。

## 与原始软件的差异

| 方面 | 原始软件 | 本项目 |
|---|---|---|
| 授权 | 闭源免费软件 | MIT 开源 |
| 平台 | 仅 Windows | Windows / macOS / Linux |
| 撤销 | 无 | Ctrl+Z |
| 清空 | 会连同截图背景一起清除 | 只清除笔迹，保留背景 |
| 保存 | 保存前重新抓屏 | 离屏重绘，结果不受其他窗口干扰 |
| 启动行为 | 每次启动写说明 txt 并自动打开 | 应用内说明窗口，不写系统目录 |
| 多显示器 | 仅主屏 | Windows 可选择全部显示器 |
| 高 DPI | 系统级 DPI 感知 | Per-Monitor V2，失败自动降级 |
| 依赖 | 打包内含 Python 3.14、Tcl/Tk 9、Pillow | Python 3.8+、Pillow、标准库 Tk |

本项目是独立实现，与原软件作者无关联，也未获得其背书。

## 开发与测试

```bash
python -m pip install -r requirements.txt
python -m pip install zstandard   # 仅提取工具的测试需要
python -m unittest discover -s tests -v
```

测试覆盖按键映射、笔迹渲染、配置合并与 Nuitka 载荷解析，共 26 项。

## 许可证

以 MIT License 发布。

Copyright (c) 2026 tsingke <tsingke@hotmail.com>

第三方组件（Pillow、Tcl/Tk、Python 等）遵循各自的许可证。

## 免责声明

本项目用于教学与屏幕标注。请勿用它截取、传播未经授权的敏感信息。逆向分析仅针对本地合法获取的软件样本，用于理解文件格式与交互设计；仓库不包含、也不再分发原软件的任何二进制或资源。

## English

Screen Whiteboard is an open-source, cross-platform screen annotation tool for teaching. A small always-on-top button sits in the corner of the screen; clicking it freezes the current screen and lets you draw on it with the mouse. Hotkeys switch colors and pen widths, clear or undo strokes, and save the result as PNG/JPEG. It runs on Windows, macOS and Linux with Python 3.8+, Tk and Pillow, and ships with a standalone extractor for Nuitka `--onefile` executables used during the reverse-engineering study. Licensed under MIT.
