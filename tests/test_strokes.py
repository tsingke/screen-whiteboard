# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from screen_whiteboard.strokes import (  # noqa: E402
    Stroke,
    compose_ink,
    render_strokes,
)


def _app():
    return QApplication.instance() or QApplication([])


class StrokeRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _app()

    def setUp(self):
        self.base = QImage(200, 200, QImage.Format_ARGB32_Premultiplied)
        self.base.fill(QColor("white"))
        self.base.setDevicePixelRatio(2.0)

    def test_size_and_dpr_preserved(self):
        image = render_strokes(self.base, [Stroke([(10, 10), (90, 90)], "#ff0000", 5)])
        self.assertEqual(image.size().width(), 200)
        self.assertEqual(image.size().height(), 200)
        self.assertEqual(image.devicePixelRatio(), 2.0)

    def test_line_is_drawn_at_physical_resolution(self):
        stroke = Stroke([(10, 10), (90, 90)], "#ff0000", 5)
        image = render_strokes(self.base, [stroke])
        color = image.pixelColor(100, 100)
        self.assertGreater(color.red(), 180)
        self.assertLess(color.green(), 90)
        self.assertLess(color.blue(), 90)

    def test_corner_stays_white(self):
        stroke = Stroke([(10, 10), (90, 90)], "#ff0000", 5)
        image = render_strokes(self.base, [stroke])
        self.assertEqual(image.pixelColor(2, 196).name(), "#ffffff")

    def test_single_point(self):
        image = render_strokes(self.base, [Stroke([(30, 30)], "#0000ff", 8)])
        color = image.pixelColor(60, 60)
        self.assertGreater(color.blue(), 180)
        self.assertLess(color.red(), 90)

    def test_empty_strokes(self):
        image = render_strokes(self.base, [])
        self.assertEqual(image.pixelColor(0, 0).name(), "#ffffff")

    def test_invalid_color_falls_back(self):
        image = render_strokes(self.base, [Stroke([(50, 50)], "not-a-color", 6)])
        color = image.pixelColor(100, 100)
        self.assertGreater(color.red(), 150)

    def test_compose_keeps_physical_pixels(self):
        from PySide6.QtGui import QPainter

        ink = QImage(200, 200, QImage.Format_ARGB32_Premultiplied)
        ink.fill(QColor(0, 0, 0, 0))
        ink.setDevicePixelRatio(2.0)
        painter = QPainter(ink)
        painter.setPen(QColor("#00ff00"))
        painter.drawPoint(30, 30)
        painter.end()

        out = compose_ink(self.base, ink)
        self.assertEqual(out.size().width(), 200)
        self.assertEqual(out.size().height(), 200)
        self.assertGreater(out.pixelColor(60, 60).green(), 150)


if __name__ == "__main__":
    unittest.main()
