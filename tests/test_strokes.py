# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import unittest

from PIL import Image

from screen_whiteboard.strokes import Stroke, render_strokes, rgb


class StrokeRenderTests(unittest.TestCase):
    def setUp(self):
        self.base = Image.new("RGB", (100, 100), "white")

    def test_size_preserved(self):
        image = render_strokes(self.base, [Stroke([(0, 0), (10, 10)], "#ff0000", 3)])
        self.assertEqual(image.size, (100, 100))

    def test_line_is_drawn(self):
        stroke = Stroke([(10, 10), (90, 90)], "#ff0000", 5)
        image = render_strokes(self.base, [stroke])
        r, g, b = image.getpixel((50, 50))[:3]
        self.assertGreater(r, 180)
        self.assertLess(g, 80)
        self.assertLess(b, 80)

    def test_corner_stays_white(self):
        stroke = Stroke([(10, 10), (90, 90)], "#ff0000", 5)
        image = render_strokes(self.base, [stroke])
        self.assertEqual(image.getpixel((2, 98))[:3], (255, 255, 255))

    def test_single_point(self):
        image = render_strokes(self.base, [Stroke([(30, 30)], "#0000ff", 7)])
        r, g, b = image.getpixel((30, 30))[:3]
        self.assertLess(r, 60)
        self.assertLess(g, 60)
        self.assertGreater(b, 180)

    def test_scale(self):
        stroke = Stroke([(10, 10), (20, 20)], "#00ff00", 2)
        image = render_strokes(self.base, [stroke], scale=2.0)
        self.assertEqual(image.size, (100, 100))
        r, g, b = image.getpixel((40, 40))[:3]
        self.assertGreater(g, 180)

    def test_empty_strokes(self):
        image = render_strokes(self.base, [])
        self.assertEqual(image.getpixel((0, 0))[:3], (255, 255, 255))

    def test_invalid_color_falls_back(self):
        self.assertEqual(len(rgb("not-a-color")), 3)


if __name__ == "__main__":
    unittest.main()
