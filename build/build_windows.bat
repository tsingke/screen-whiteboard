@echo off
setlocal
cd /d "%~dp0.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --clean --onedir --windowed ^
  --workpath build\pyinstaller --distpath dist ^
  --name ScreenWhiteboard ^
  --icon assets\screen-whiteboard.ico ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtMultimedia ^
  main.py

echo.
echo 构建完成：dist\ScreenWhiteboard\ScreenWhiteboard.exe
endlocal
