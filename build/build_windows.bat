@echo off
setlocal
cd /d "%~dp0.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name ScreenWhiteboard ^
  --icon assets\screen-whiteboard.ico ^
  main.py

echo.
echo 构建完成：dist\ScreenWhiteboard.exe
endlocal
