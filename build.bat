@echo off
echo ============================================
echo  Pomodoro Timer - EXE wird erstellt ...
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH.
    echo Bitte Python von https://python.org herunterladen.
    pause
    exit /b 1
)

echo [1/3] PyInstaller installieren ...
pip install pyinstaller --quiet

echo.
echo [2/3] EXE erstellen ...
pyinstaller --onefile --windowed ^
            --name "PomodoroTimer" ^
            --icon "pomodoro_timer.ico" ^
            --add-data "pomodoro_timer.ico;." ^
            pomodoro.py

echo.
echo [3/3] Fertig!
echo.
if exist "dist\PomodoroTimer.exe" (
    echo  Die EXE liegt unter:  dist\PomodoroTimer.exe
    echo  Einfach doppelklicken zum Starten.
) else (
    echo  FEHLER: EXE wurde nicht erstellt. Siehe Log oben.
)
echo.
pause
