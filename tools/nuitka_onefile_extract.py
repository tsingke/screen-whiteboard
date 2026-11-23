#!/usr/bin/env python3
# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""提取 Nuitka --onefile 可执行文件中的内嵌文件。

适用格式（旧版 onefile）：

    "KA" + 压缩方式字节 + zstd 帧
    解压后为若干条 [UTF-16LE 文件名][u64 小端长度][文件数据]

不执行、不加载被提取的内容；只做字节级解析。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Tuple

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
MAGIC_PREFIX = b"KA"


class ExtractError(RuntimeError):
    pass


@dataclass
class Entry:
    name: str
    size: int
    offset: int


def find_payload_candidates(data: bytes) -> Iterable[Tuple[int, int]]:
    """产出 (zstd 帧偏移, KA 魔数偏移)。

    Nuitka 的魔数为 3 字节：'K' 'A' + 压缩方式；压缩方式后紧跟 zstd 帧。
    """
    start = 0
    while True:
        frame = data.find(ZSTD_MAGIC, start)
        if frame < 0:
            return
        start = frame + 1
        if frame >= 3 and data[frame - 3:frame - 1] == MAGIC_PREFIX:
            yield frame - 3, frame


def _decompress_with_module(frame: bytes) -> Optional[bytes]:
    try:
        import zstandard as zstd  # type: ignore
    except ImportError:
        return None

    try:
        obj = zstd.ZstdDecompressor().decompressobj()
        chunks = []
        step = 1 << 20
        for start in range(0, len(frame), step):
            chunk = frame[start:start + step]
            if chunk:
                chunks.append(obj.decompress(chunk))
            if obj.eof:
                # 帧已经结束，末尾可能跟着 PE 对齐数据，停止喂入。
                break
        if not obj.eof:
            raise ExtractError("zstd 数据不完整（未读到帧结尾）。")
        return b"".join(chunks)
    except zstd.ZstdError as exc:
        raise ExtractError(f"zstd 解压失败：{exc}") from exc


def _decompress_with_cli(frame: bytes) -> bytes:
    exe = shutil.which("zstd")
    if not exe:
        raise ExtractError(
            "需要 zstandard 模块或 zstd 命令行工具：\n"
            "  python -m pip install zstandard\n"
            "或安装系统包 zstd。"
        )
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "payload.zst"
        src.write_bytes(frame)
        result = subprocess.run(
            [exe, "-d", "-c", str(src)],
            capture_output=True,
        )
        if result.returncode != 0:
            raise ExtractError(
                "zstd 解压失败：" + result.stderr.decode("utf-8", "replace").strip()
            )
        return result.stdout


def decompress_payload(frame: bytes) -> bytes:
    data = _decompress_with_module(frame)
    if data is None:
        data = _decompress_with_cli(frame)
    return data


def parse_entries(payload: bytes) -> List[Entry]:
    entries: List[Entry] = []
    pos = 0
    total = len(payload)
    while pos < total:
        start = pos
        end = start
        while end + 1 < total and payload[end:end + 2] != b"\x00\x00":
            end += 2
        if end + 1 >= total:
            break
        try:
            name = payload[start:end].decode("utf-16le")
        except UnicodeDecodeError as exc:
            raise ExtractError(f"文件名解码失败（偏移 {start:#x}）：{exc}") from exc
        pos = end + 2
        if pos + 8 > total:
            break
        size = struct.unpack_from("<Q", payload, pos)[0]
        pos += 8
        if size > total - pos:
            raise ExtractError(
                f"条目长度越界：{name!r} 声明 {size} 字节，剩余 {total - pos} 字节"
            )
        entries.append(Entry(name=name, size=size, offset=pos))
        pos += size

    if not entries:
        raise ExtractError("未解析到任何文件条目，可能不是旧版 Nuitka onefile 格式。")
    if pos != total:
        # 允许末尾有少量对齐零字节
        tail = payload[pos:]
        if tail.strip(b"\x00"):
            raise ExtractError(
                f"条目解析在 {pos:#x}/{total:#x} 处提前结束，格式可能不完整。"
            )
    return entries


def locate_and_decompress(
    data: bytes,
    dump_payload: Optional[pathlib.Path] = None,
) -> Tuple[bytes, List[Entry], int]:
    errors: List[str] = []
    for magic_offset, frame_offset in find_payload_candidates(data):
        try:
            payload = decompress_payload(data[frame_offset:])
            entries = parse_entries(payload)
            if dump_payload is not None:
                dump_payload.write_bytes(payload)
            return payload, entries, magic_offset
        except ExtractError as exc:
            errors.append(f"{magic_offset:#x}: {exc}")
            continue
    detail = "\n".join("  " + line for line in errors[:5])
    raise ExtractError(
        "没有找到可解析的 Nuitka onefile 载荷。\n" + (detail if detail else "")
    )


def safe_relative_name(name: str, keep_paths: bool) -> str:
    """把内嵌文件名转换成安全的相对路径，拒绝目录穿越。"""
    normalized = name.replace("\\", "/")
    if keep_paths:
        parts = [p for p in normalized.split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts):
            raise ExtractError(f"拒绝包含 '..' 的路径：{name!r}")
        if any(os.path.isabs(p) or (len(p) > 1 and p[1] == ":") for p in parts):
            raise ExtractError(f"拒绝绝对路径：{name!r}")
        return os.path.join(*parts) if parts else "_unnamed_"
    return normalized.replace("/", "__")


def _write_entries(payload: bytes, entries: List[Entry], out_dir: pathlib.Path,
                   keep_paths: bool) -> None:
    for entry in entries:
        relative = safe_relative_name(entry.name, keep_paths)
        target = out_dir / relative
        try:
            target.relative_to(out_dir)
        except ValueError as exc:
            raise ExtractError(f"拒绝写出到目标目录之外：{entry.name!r}") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload[entry.offset:entry.offset + entry.size])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="从 Nuitka --onefile 生成的 Windows 可执行文件中提取内嵌文件。",
    )
    parser.add_argument("exe", type=pathlib.Path, help="待分析的可执行文件")
    parser.add_argument("-o", "--out", type=pathlib.Path, default=None, help="输出目录")
    parser.add_argument("--list", action="store_true", help="只列出文件，不解包")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出文件清单")
    parser.add_argument("--keep-paths", action="store_true", help="保留内部目录结构")
    parser.add_argument("--force", action="store_true", help="允许写入非空输出目录")
    parser.add_argument("--dump-payload", type=pathlib.Path, default=None,
                        help="额外保存解压后的原始载荷（便于进一步分析）")
    args = parser.parse_args(argv)

    if not args.exe.is_file():
        print(f"文件不存在：{args.exe}", file=sys.stderr)
        return 2

    out_dir = args.out or (pathlib.Path.cwd() / f"{args.exe.stem}_extracted")
    try:
        data = args.exe.read_bytes()
        print(f"文件：{args.exe}")
        print(f"大小：{len(data):,} 字节")
        print(f"SHA-256：{hashlib.sha256(data).hexdigest()}")

        payload, entries, magic_offset = locate_and_decompress(
            data, dump_payload=args.dump_payload
        )
        print(f"载荷魔数偏移：{magic_offset:#x}")
        print(f"解压后大小：{len(payload):,} 字节")
        print(f"文件条目：{len(entries)}")

        if args.json:
            print(json.dumps([asdict(e) for e in entries], ensure_ascii=False, indent=2))
            return 0
        if args.list:
            for entry in entries:
                print(f"{entry.size:>12}  {entry.name}")
            return 0

        if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
            print(
                f"输出目录非空：{out_dir}\n如需覆盖，请加 --force 或换一个目录。",
                file=sys.stderr,
            )
            return 3
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_entries(payload, entries, out_dir, args.keep_paths)
        print(f"已写出到：{out_dir}")
        return 0
    except ExtractError as exc:
        print(f"提取失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
