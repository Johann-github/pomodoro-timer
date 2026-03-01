# 🍅 Pomodoro Timer

A clean, dark-mode Pomodoro timer app built with Python and tkinter — packaged as a standalone Windows EXE.

## Features

- **Timer** with circular progress ring for Work, Short Break, and Long Break
- **Pomodoro cycles** — adjustable from 2 to 8 cycles with −/+ buttons
- **Custom break schedule** — set each cycle individually to short or long break
- **Inline notifications** — session-done banner instead of popup windows
- **To-Do list** — add tasks, check them off, archive completed ones
- **Archive page** — view and manage all archived tasks inline
- **Settings** (via ☰ menu):
  - Adjust break durations
  - Customize accent colors for each mode
  - Switch between 🌙 Dark and ☀️ Light mode
  - Switch between 🇩🇪 Deutsch and 🇬🇧 English
- **Mute toggle** for session-done sound
- All settings are saved automatically and persist across restarts

## Requirements

- Python 3.10+
- tkinter (included with Python on Windows)
- PyInstaller (for building the EXE)

## Run from source

```bash
python pomodoro.py
```

## Build the EXE

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "PomodoroTimer" --icon "pomodoro_timer.ico" --add-data "pomodoro_timer.ico;." pomodoro.py
```

The executable will be created in the `dist/` folder.
