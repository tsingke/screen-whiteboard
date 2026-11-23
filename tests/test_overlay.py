# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage, QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from screen_whiteboard.capture import Capture  # noqa: E402
from screen_whiteboard.config import Settings  # noqa: E402
from screen_whiteboard.overlay import Overlay  # noqa: E402


def _app():
    return QApplication.instance() or QApplication([])


def _mouse(kind, x, y):
    point = QPointF(x, y)
    return QMouseEvent(
        kind, point, point, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier
    )


class OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _app()

    def setUp(self):
        image = QImage(400, 200, QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor("white"))
        image.setDevicePixelRatio(2.0)
        self.capture = Capture(image, 200, 100, 0, 0, 2.0)
        self.settings = Settings()
        self.settings.default_color = "r"
        self.settings.default_width = 4
        self.overlay = Overlay(self.capture, self.settings)

    def tearDown(self):
        self.overlay.close()

    def test_stroke_recording_and_physical_ink(self):
        self.overlay.mousePressEvent(
            _mouse(QEvent.MouseButtonPress, 10, 10)
        )
        self.overlay.mouseMoveEvent(
            _mouse(QEvent.MouseMove, 60, 50)
        )
        self.overlay.mouseReleaseEvent(
            _mouse(QEvent.MouseButtonRelease, 60, 50)
        )
        self.assertEqual(len(self.overlay.strokes), 1)
        self.assertGreaterEqual(len(self.overlay.strokes[0].points), 2)
        # 逻辑坐标 (10,10) 对应物理像素 (20,20)
        color = self.overlay.ink.pixelColor(20, 20)
        self.assertGreater(color.red(), 150)

    def test_undo_and_clear(self):
        self.overlay.mousePressEvent(_mouse(QEvent.MouseButtonPress, 5, 5))
        self.overlay.mouseReleaseEvent(_mouse(QEvent.MouseButtonRelease, 5, 5))
        self.assertEqual(len(self.overlay.strokes), 1)
        self.overlay.undo()
        self.assertEqual(len(self.overlay.strokes), 0)
        self.assertEqual(
            self.overlay.ink.pixelColor(10, 10).alpha(), 0
        )
        self.overlay.mousePressEvent(_mouse(QEvent.MouseButtonPress, 5, 5))
        self.overlay.mouseReleaseEvent(_mouse(QEvent.MouseButtonRelease, 5, 5))
        self.overlay.clear()
        self.assertEqual(len(self.overlay.strokes), 0)

    def test_key_changes_color_and_width(self):
        self.overlay.keyPressEvent(
            self._key("g", Qt.Key_G)
        )
        self.assertEqual(self.overlay.color.lower(), self.settings.colors["g"].lower())
        self.overlay.keyPressEvent(
            self._key("7", Qt.Key_7)
        )
        self.assertEqual(self.overlay.width, 7)

    def _key(self, text, key):
        from PySide6.QtGui import QKeyEvent

        return QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, text)


if __name__ == "__main__":
    unittest.main()
