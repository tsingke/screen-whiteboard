# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""应用内使用说明与关于窗口。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .config import Settings

HELP_HTML = """
<h3>开始标注</h3>
<p>点击屏幕右上角的「开始手写」按钮，当前画面会冻结并被覆盖，
此时可以用鼠标左键自由书写、画线。</p>

<h3>退出程序</h3>
<p>在「开始手写」按钮上单击鼠标右键。按钮可以用左键拖动到屏幕任意位置。</p>

<h3>标注模式快捷键</h3>
<table cellspacing="0" cellpadding="6" width="100%">
<tr><td width="42%"><b>R / G / B</b></td><td>红、绿、蓝</td></tr>
<tr><td><b>Y / K / W</b></td><td>黄、黑、白</td></tr>
<tr><td><b>1 ~ 9</b></td><td>线条粗细</td></tr>
<tr><td><b>C</b></td><td>清除全部笔迹</td></tr>
<tr><td><b>Ctrl + Z</b></td><td>撤销上一笔</td></tr>
<tr><td><b>S / Ctrl + S</b></td><td>保存截图（PNG / JPEG）</td></tr>
<tr><td><b>Esc</b></td><td>退出标注模式</td></tr>
</table>

<h3>小提示</h3>
<ul>
<li>标注模式会截取当前屏幕，动手前请先准备好要讲的内容。</li>
<li>macOS 首次使用需要在「系统设置 → 隐私与安全性 → 屏幕录制」中授权。</li>
<li>Windows 可在启动参数中使用 <code>--all-monitors</code> 覆盖全部显示器。</li>
<li>画面按屏幕物理像素截取与渲染，Retina / 高 DPI 屏幕上不会发虚。</li>
</ul>

<h3>关于</h3>
<p>屏幕白板是一个独立开发的开源项目，以 MIT 许可发布。
代码、图标与说明文本均为原创，不包含任何第三方软件的代码或资源。</p>
"""


class HelpDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("使用说明 · 屏幕白板")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setFixedSize(640, 620)
        self.setStyleSheet(
            """
            QDialog { background: #f6f7fb; }
            QLabel#header {
                color: white;
                font-size: 20px;
                font-weight: 600;
                padding-left: 26px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6c4cf1, stop:1 #9b6bff);
            }
            QTextBrowser {
                background: #ffffff;
                border: 1px solid #e6e8f2;
                border-radius: 12px;
                padding: 14px 18px;
                color: #2b2d3a;
                font-size: 14px;
            }
            QLabel#version { color: #8b90a3; font-size: 12px; }
            QPushButton#primary {
                background: #6c4cf1;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 9px 24px;
                font-weight: 600;
            }
            QPushButton#primary:hover { background: #7d5cf5; }
            QPushButton#primary:pressed { background: #5b3fe6; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("屏幕白板 · 使用说明")
        header.setObjectName("header")
        header.setFixedHeight(76)
        layout.addWidget(header)

        body = QTextBrowser()
        body.setOpenExternalLinks(False)
        body.setHtml(HELP_HTML)

        body_container = QWidget()
        body_layout = QVBoxLayout(body_container)
        body_layout.setContentsMargins(20, 16, 20, 0)
        body_layout.addWidget(body)
        layout.addWidget(body_container, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(20, 14, 20, 16)
        version = QLabel(f"v{__version__}  ·  MIT License")
        version.setObjectName("version")
        footer.addWidget(version)
        footer.addStretch(1)
        close_button = QPushButton("知道了")
        close_button.setObjectName("primary")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        self._center()

    def _center(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.center().x() - self.width() // 2,
            area.center().y() - self.height() // 2,
        )

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.accept()
            return
        super().keyPressEvent(event)
