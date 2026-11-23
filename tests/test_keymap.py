# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import unittest

from screen_whiteboard.keymap import ActionType, resolve_key

COLORS = {"r": "#ff0000", "g": "#00ff00", "b": "#0000ff"}


class KeymapTests(unittest.TestCase):
    def test_escape_closes(self):
        action = resolve_key("", "Escape", colors=COLORS)
        self.assertIs(action.type, ActionType.CLOSE)

    def test_ctrl_z_undo(self):
        action = resolve_key("\x1a", "z", ctrl=True, colors=COLORS)
        self.assertIs(action.type, ActionType.UNDO)

    def test_ctrl_s_saves(self):
        action = resolve_key("\x13", "s", ctrl=True, colors=COLORS)
        self.assertIs(action.type, ActionType.SAVE)

    def test_colors(self):
        for key, value in COLORS.items():
            action = resolve_key(key, key, colors=COLORS)
            self.assertIs(action.type, ActionType.COLOR)
            self.assertEqual(action.value, value)

    def test_uppercase_color(self):
        action = resolve_key("R", "r", colors=COLORS)
        self.assertIs(action.type, ActionType.COLOR)
        self.assertEqual(action.value, "#ff0000")

    def test_widths(self):
        for digit in "123456789":
            action = resolve_key(digit, digit, colors=COLORS)
            self.assertIs(action.type, ActionType.WIDTH)
            self.assertEqual(action.value, int(digit))

    def test_clear(self):
        self.assertIs(resolve_key("c", "c", colors=COLORS).type, ActionType.CLEAR)

    def test_save(self):
        self.assertIs(resolve_key("s", "s", colors=COLORS).type, ActionType.SAVE)

    def test_unknown_key(self):
        self.assertIs(resolve_key("q", "q", colors=COLORS).type, ActionType.NONE)

    def test_ctrl_does_not_break_colors(self):
        action = resolve_key("r", "r", ctrl=True, colors=COLORS)
        self.assertIs(action.type, ActionType.COLOR)


if __name__ == "__main__":
    unittest.main()
