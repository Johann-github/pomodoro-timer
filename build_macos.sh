#!/bin/bash
# Build script for macOS .app bundle
# Run this on a Mac with Python 3.10+ installed.
#
# Usage:
#   chmod +x build_macos.sh
#   ./build_macos.sh

set -e

echo "Installing PyInstaller..."
pip install pyinstaller

echo "Building PomodoroTimer.app..."
python -m PyInstaller \
    --onefile \
    --windowed \
    --name "PomodoroTimer" \
    pomodoro.py

echo ""
echo "Done! The app is at: dist/PomodoroTimer"
echo ""
echo "To create a .app bundle (drag-and-drop installable), use --windowed"
echo "which PyInstaller already handles above. The .app is inside dist/."
echo ""
echo "Optional: to add a dock icon, convert pomodoro_timer.ico to .icns first:"
echo "  sips -s format icns pomodoro_timer.ico --out pomodoro_timer.icns"
echo "Then add --icon pomodoro_timer.icns to the PyInstaller command."
