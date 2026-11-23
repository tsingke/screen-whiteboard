#!/usr/bin/env bash
# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --clean --windowed \
  --name ScreenWhiteboard \
  --osx-bundle-identifier io.github.tsingke.screenwhiteboard \
  --icon assets/screen-whiteboard.icns \
  main.py

echo
echo "构建完成：dist/ScreenWhiteboard.app"
