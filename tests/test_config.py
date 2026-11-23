# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
from pathlib import Path

from screen_whiteboard.config import Settings, load_settings, save_settings


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = load_settings(Path(tmp) / "missing.json")
        self.assertEqual(settings.default_width, 3)
        self.assertIn("r", settings.colors)

    def test_merge_valid_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps({"default_width": 7, "offset_x": 0, "unknown": 1}),
                encoding="utf-8",
            )
            settings = load_settings(path)
        self.assertEqual(settings.default_width, 7)
        self.assertEqual(settings.offset_x, 0)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{not json", encoding="utf-8")
            settings = load_settings(path)
        self.assertIsInstance(settings, Settings)

    def test_clamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"default_width": 999, "hide_delay": -5}), encoding="utf-8")
            settings = load_settings(path)
        self.assertLessEqual(settings.default_width, settings.max_width)
        self.assertEqual(settings.hide_delay, 0.0)

    def test_save_roundtrip(self):
        settings = Settings()
        settings.default_width = 5
        with tempfile.TemporaryDirectory() as tmp:
            path = save_settings(settings, Path(tmp) / "sub" / "config.json")
            loaded = load_settings(path)
        self.assertEqual(loaded.default_width, 5)
        self.assertEqual(loaded.launcher_text, settings.launcher_text)


if __name__ == "__main__":
    unittest.main()
