# 🍅 Pomodoro Timer

A clean, dark-mode Pomodoro timer app available as a Windows desktop app (Python/tkinter) and a browser-based web app (vanilla HTML/CSS/JS).

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

## Web Version

Open `web/index.html` in any modern browser — no installation required.

## Desktop Version (Windows)

### Requirements

- Python 3.10+
- tkinter (included with Python on Windows)
- PyInstaller (for building the EXE)

### Run from source

```bash
python pomodoro.py
```

### Build the EXE

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "PomodoroTimer" --icon "pomodoro_timer.ico" --add-data "pomodoro_timer.ico;." pomodoro.py
```

The executable will be created in the `dist/` folder.

## Roadmap

### ✅ Done
- [x] Windows desktop app (Python + tkinter)
- [x] Circular progress timer with Work / Short Break / Long Break
- [x] Adjustable Pomodoro cycles (2–8) with custom break schedule
- [x] Inline session notifications (no popup windows)
- [x] To-Do list with archive
- [x] Dark / Light mode
- [x] Custom accent colors per mode
- [x] German / English language support
- [x] Settings persist across restarts
- [x] Web version — single-file browser app (vanilla HTML/CSS/JS, no build step)

### 🚧 Planned
- [ ] **macOS version** — native `.app` bundle via PyInstaller for macOS
- [ ] **iOS app** — native timer app for iPhone / iPad
- [ ] **Android app** — native timer app for Android
- [ ] **Cross-platform task sync** — sync To-Do list and settings across all devices via cloud backend
