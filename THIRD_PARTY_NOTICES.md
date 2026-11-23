# 第三方组件声明

屏幕白板自身的源代码、图标与文档以 MIT License 发布，版权归张庆科所有。

运行时依赖以下通用开源组件，它们遵循各自的许可证：

| 组件 | 许可证 | 说明 |
|---|---|---|
| Python | PSF License | https://docs.python.org/3/license.html |
| PySide6 | LGPLv3 / GPLv3 / 商业许可 | https://www.qt.io/qt-licensing |
| Qt 6 | LGPLv3 / GPLv3 / 商业许可 | https://www.qt.io/qt-licensing |
| PyInstaller（仅构建时） | GPLv2 with Bootloader Exception | https://pyinstaller.org/en/stable/license.html |

PySide6 与 Qt 以动态链接方式使用，发布包中包含其运行库。根据 LGPLv3，使用者有权替换这些库：

- Windows 目录版：替换 `ScreenWhiteboard/` 目录下的 Qt 动态库后重新启动即可。
- macOS App：可在 `ScreenWhiteboard.app/Contents/Frameworks/` 中替换对应的 Qt 框架。

如需获取 PySide6 / Qt 的完整源代码，请访问 https://download.qt.io/ 或 https://pypi.org/project/PySide6/。

本项目不包含、也不再分发任何其他软件的代码、图像或文本资源。
