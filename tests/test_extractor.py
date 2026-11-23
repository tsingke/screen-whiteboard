# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

import struct
import unittest

from tools.nuitka_onefile_extract import (
    ExtractError,
    locate_and_decompress,
    parse_entries,
    safe_relative_name,
)

try:
    import zstandard  # type: ignore
except ImportError:  # 允许在未安装依赖时跳过压缩相关测试
    zstandard = None


def build_payload(items):
    chunks = []
    for name, data in items:
        chunks.append(name.encode("utf-16le") + b"\x00\x00")
        chunks.append(struct.pack("<Q", len(data)))
        chunks.append(data)
    return b"".join(chunks)


class ParseTests(unittest.TestCase):
    def test_parse_roundtrip(self):
        payload = build_payload([
            ("a.txt", b"hello"),
            ("PIL\\_imaging.pyd", bytes(range(32))),
        ])
        entries = parse_entries(payload)
        self.assertEqual([e.name for e in entries], ["a.txt", "PIL\\_imaging.pyd"])
        self.assertEqual(entries[0].size, 5)
        self.assertEqual(entries[1].size, 32)

    def test_bad_size(self):
        payload = "x".encode("utf-16le") + b"\x00\x00" + struct.pack("<Q", 9999) + b"short"
        with self.assertRaises(ExtractError):
            parse_entries(payload)

    def test_safe_names(self):
        self.assertEqual(safe_relative_name("PIL\\x.pyd", keep_paths=False), "PIL__x.pyd")
        with self.assertRaises(ExtractError):
            safe_relative_name("../evil.txt", keep_paths=True)
        with self.assertRaises(ExtractError):
            safe_relative_name("C:\\evil.txt", keep_paths=True)

    @unittest.skipIf(zstandard is None, "未安装 zstandard")
    def test_end_to_end(self):
        payload = build_payload([("hello.txt", b"hello world")])
        compressed = zstandard.ZstdCompressor().compress(payload)
        blob = b"\x00" * 64 + b"KAY" + compressed + b"\x00" * 32
        recovered, entries, offset = locate_and_decompress(blob)
        self.assertEqual(offset, 64)
        self.assertEqual(recovered, payload)
        self.assertEqual(entries[0].name, "hello.txt")


if __name__ == "__main__":
    unittest.main()
