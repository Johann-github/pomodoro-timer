import tkinter as tk
from tkinter import colorchooser
import threading
import time as _time_mod
import json
import pathlib
import sys
import math
import struct
import wave
import tempfile
import os
import subprocess

# ── Translations ─────────────────────────────────────────────────────────────

STRINGS = {
    "de": {
        "work": "Arbeitszeit", "short_break": "Kurze Pause", "long_break": "Lange Pause",
        "start": "▶  Start", "pause": "⏸  Pause", "resume": "▶  Fortsetzen",
        "reset": "↺  Reset", "skip": "⏭  Überspringen",
        "tasks_header": "Aufgaben", "archive_btn": "→ Archivieren",
        "archive_title": "📦  Archiv", "delete_all": "Alle löschen",
        "no_archived": "Noch keine archivierten Aufgaben.",
        "break_times": "Pausenzeiten",
        "short_min": "Kurze Pause (Minuten)", "long_min": "Lange Pause (Minuten)",
        "break_schedule": "Pausenplan",
        "save": "Speichern", "cancel": "Abbrechen",
        "menu_mute": "🔔  Ton an/aus", "menu_muted": "🔇  Ton (stumm)",
        "menu_settings": "⚙️  Einstellungen", "menu_archive": "📦  Archiv",
        "done_long": "Lange Pause verdient! Gut gemacht.",
        "done_short": "Kurze Pause verdient! Gleich weiter.",
        "done_work": "Pause vorbei – zurück an die Arbeit!",
        "ok_start": "OK  ▶",
        "colors_section": "Farben",
        "color_work": "Arbeitszeit", "color_short": "Kurze Pause", "color_long": "Lange Pause",
        "appearance": "Erscheinungsbild",
        "dark_btn": "🌙  Dark", "light_btn": "☀️  Light",
        "language": "Sprache",
        "settings_title": "⚙️  Einstellungen",
        "choose_color": "Farbe wählen",
    },
    "en": {
        "work": "Work Time", "short_break": "Short Break", "long_break": "Long Break",
        "start": "▶  Start", "pause": "⏸  Pause", "resume": "▶  Resume",
        "reset": "↺  Reset", "skip": "⏭  Skip",
        "tasks_header": "Tasks", "archive_btn": "→ Archive",
        "archive_title": "📦  Archive", "delete_all": "Delete all",
        "no_archived": "No archived tasks yet.",
        "break_times": "Break Times",
        "short_min": "Short Break (minutes)", "long_min": "Long Break (minutes)",
        "break_schedule": "Break Schedule",
        "save": "Save", "cancel": "Cancel",
        "menu_mute": "🔔  Sound on/off", "menu_muted": "🔇  Sound (muted)",
        "menu_settings": "⚙️  Settings", "menu_archive": "📦  Archive",
        "done_long": "Long break earned! Well done.",
        "done_short": "Short break earned! Back soon.",
        "done_work": "Break over – back to work!",
        "ok_start": "OK  ▶",
        "colors_section": "Colors",
        "color_work": "Work Time", "color_short": "Short Break", "color_long": "Long Break",
        "appearance": "Appearance",
        "dark_btn": "🌙  Dark", "light_btn": "☀️  Light",
        "language": "Language",
        "settings_title": "⚙️  Settings",
        "choose_color": "Choose color",
    },
}

# ── Themes ────────────────────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "BG": "#1e1e1e", "BG2": "#2a2a2a", "BG3": "#2e2e2e",
        "FG": "#ffffff", "FG_DIM": "#888888",
        "ARC_BG": "#333333", "SEP": "#333333", "SEL_CHK": "#333333",
    },
    "light": {
        "BG": "#f0f0f0", "BG2": "#e2e2e2", "BG3": "#d0d0d0",
        "FG": "#1a1a1a", "FG_DIM": "#555555",
        "ARC_BG": "#bbbbbb", "SEP": "#cccccc", "SEL_CHK": "#c0c0c0",
    },
}


class PomodoroApp:
    WORK_TIME  = 25 * 60
    SHORT_BREAK = 5 * 60
    LONG_BREAK  = 15 * 60
    CYCLES_BEFORE_LONG_BREAK = 4
    ACCENT_SEL = "#4a7fc1"   # highlight colour for selected buttons

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("380x780")
        self.root.minsize(380, 640)
        self.root.resizable(False, True)

        self.mode = "work"
        self.running = False
        self.cycles_done = 0
        self._job = None

        self._todos: list[tuple[tk.BooleanVar, tk.Frame, str]] = []
        self._archived: list[str] = []
        self._muted = False
        self._menu_open = False
        self._current_page = "main"
        self._notif_job = None
        self._color_btns: dict[str, tk.Button] = {}

        self._lang     = "de"
        self._theme    = "dark"
        self._pet_type = "cat"
        self._apply_theme_colors()

        s = STRINGS[self._lang]
        self.MODES = {
            "work":        (s["work"],        "#e74c3c", self.WORK_TIME),
            "short_break": (s["short_break"], "#27ae60", self.SHORT_BREAK),
            "long_break":  (s["long_break"],  "#2980b9", self.LONG_BREAK),
        }
        self.cycles_max = self.CYCLES_BEFORE_LONG_BREAK
        self._break_schedule: list[str] = (
            ["short_break"] * (self.cycles_max - 1) + ["long_break"]
        )
        self._load_config()
        self.time_left = self.MODES["work"][2]

        self.root.configure(bg=self.BG)
        self._build_ui()
        self._refresh()

    def _apply_theme_colors(self) -> None:
        th = THEMES[self._theme]
        self.BG     = th["BG"]
        self.BG2    = th["BG2"]
        self.BG3    = th["BG3"]
        self.FG     = th["FG"]
        self.FG_DIM = th["FG_DIM"]

    # ------------------------------------------------------------------ UI --

    def _build_ui(self) -> None:
        s = STRINGS[self._lang]

        # ── Header ──────────────────────────────────────────────────────────
        self._header_frame = tk.Frame(self.root, bg=self.BG)
        self._header_frame.pack(fill=tk.X, padx=16, pady=(14, 4))
        self._header_frame.grid_columnconfigure(1, weight=1)

        self._back_btn = tk.Button(
            self._header_frame, text="←",
            font=("Segoe UI", 15),
            bg=self.BG, fg=self.FG_DIM,
            activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2",
            command=self._go_main,
        )
        self._back_btn.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._back_btn.grid_remove()

        tk.Label(
            self._header_frame, text="Pomodoro Timer",
            font=("Segoe UI", 17, "bold"),
            bg=self.BG, fg=self.FG,
        ).grid(row=0, column=1)

        self._menu_btn = tk.Button(
            self._header_frame, text="☰",
            font=("Segoe UI", 16),
            bg=self.BG, fg=self.FG_DIM,
            activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2",
            command=self._toggle_menu,
        )
        self._menu_btn.grid(row=0, column=2, sticky="e")

        # ── Notification bar ─────────────────────────────────────────────────
        self._notif_frame = tk.Frame(self.root, bg="#203a28")
        self._notif_label = tk.Label(
            self._notif_frame, text="",
            font=("Segoe UI", 11), bg="#203a28", fg=self.FG,
            wraplength=270, anchor="w",
        )
        self._notif_label.pack(side=tk.LEFT, padx=(14, 8), pady=10, expand=True, fill=tk.X)
        self._notif_btn = tk.Button(
            self._notif_frame, text=s["ok_start"],
            font=("Segoe UI", 10, "bold"),
            bg="#27ae60", fg=self.FG, activebackground="#219a52",
            padx=14, pady=6, bd=0, relief="flat", cursor="hand2",
            command=self._notif_ok,
        )
        self._notif_btn.pack(side=tk.RIGHT, padx=(0, 14), pady=10)

        # ── Hamburger overlay ─────────────────────────────────────────────────
        self._menu_overlay = tk.Frame(self.root, bg=self.BG2, bd=1, relief="solid")

        self._mute_menu_btn = tk.Button(
            self._menu_overlay,
            text=s["menu_muted"] if self._muted else s["menu_mute"],
            font=("Segoe UI", 11),
            bg=self.BG2, fg=self.FG,
            activebackground=self.BG3, activeforeground=self.FG,
            anchor="w", padx=16, pady=8, bd=0, relief="flat", cursor="hand2", width=16,
            command=self._menu_mute,
        )
        self._mute_menu_btn.pack(fill=tk.X)

        tk.Button(
            self._menu_overlay, text=s["menu_settings"],
            font=("Segoe UI", 11),
            bg=self.BG2, fg=self.FG,
            activebackground=self.BG3, activeforeground=self.FG,
            anchor="w", padx=16, pady=8, bd=0, relief="flat", cursor="hand2", width=16,
            command=self._menu_settings,
        ).pack(fill=tk.X)

        tk.Button(
            self._menu_overlay, text=s["menu_archive"],
            font=("Segoe UI", 11),
            bg=self.BG2, fg=self.FG,
            activebackground=self.BG3, activeforeground=self.FG,
            anchor="w", padx=16, pady=8, bd=0, relief="flat", cursor="hand2", width=16,
            command=self._menu_archive,
        ).pack(fill=tk.X)

        self.root.bind("<Button-1>", self._on_root_click)

        # ── Content area ──────────────────────────────────────────────────────
        self._content = tk.Frame(self.root, bg=self.BG)
        self._content.pack(fill=tk.BOTH, expand=True)

        self._build_main_page()
        self._build_archive_page()
        self._build_settings_page()
        self._show_page("main")

    # ──────────────────────────────────────────────────────────── Pages ──

    def _show_page(self, name: str) -> None:
        for pname, frame in (
            ("main",     self._page_main),
            ("archive",  self._page_archive),
            ("settings", self._page_settings),
        ):
            (frame.pack if pname == name else frame.pack_forget)(
                **({"fill": tk.BOTH, "expand": True} if pname == name else {})
            )
        if name == "main":
            self._back_btn.grid_remove()
        else:
            self._back_btn.grid()
        self._current_page = name

    def _go_main(self) -> None:
        self._show_page("main")

    # ─────────────────────────────────────────────────── Main page ──

    def _build_main_page(self) -> None:
        s  = STRINGS[self._lang]
        th = THEMES[self._theme]
        self._page_main = tk.Frame(self._content, bg=self.BG)

        self.mode_label = tk.Label(
            self._page_main, text="",
            font=("Segoe UI", 11), bg=self.BG, fg=self.FG_DIM,
        )
        self.mode_label.pack()

        self.canvas = tk.Canvas(
            self._page_main, width=220, height=220,
            bg=self.BG, highlightthickness=0,
        )
        self.canvas.pack(pady=10)
        self.canvas.create_arc(
            12, 12, 208, 208, start=90, extent=359.99,
            outline=th["ARC_BG"], width=10, style="arc",
        )
        self._arc = self.canvas.create_arc(
            12, 12, 208, 208, start=90, extent=359.99,
            outline="#e74c3c", width=10, style="arc",
        )
        self._time_text = self.canvas.create_text(
            110, 110, text="25:00",
            font=("Segoe UI", 42, "bold"), fill=self.FG,
        )
        self.canvas.tag_bind(self._time_text, "<Button-1>", lambda _e: self._edit_time())
        self.canvas.tag_bind(self._time_text, "<Enter>",
                             lambda _e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(self._time_text, "<Leave>",
                             lambda _e: self.canvas.config(cursor=""))

        dots_row = tk.Frame(self._page_main, bg=self.BG)
        dots_row.pack(pady=2)
        self._minus_btn = tk.Button(
            dots_row, text="−", font=("Segoe UI", 14, "bold"),
            bg=self.BG, fg=self.FG_DIM, activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2", width=2,
            command=lambda: self._adjust_cycles(-1),
        )
        self._minus_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.dots_label = tk.Label(
            dots_row, text="", font=("Segoe UI", 16), bg=self.BG,
        )
        self.dots_label.pack(side=tk.LEFT)
        self._plus_btn = tk.Button(
            dots_row, text="+", font=("Segoe UI", 14, "bold"),
            bg=self.BG, fg=self.FG_DIM, activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2", width=2,
            command=lambda: self._adjust_cycles(+1),
        )
        self._plus_btn.pack(side=tk.LEFT, padx=(4, 0))

        btn_row = tk.Frame(self._page_main, bg=self.BG)
        btn_row.pack(pady=12)
        self.start_btn = self._make_btn(btn_row, s["start"], self.toggle, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=8)
        self._make_btn(btn_row, s["reset"], self.reset, bg="#444444", width=9).pack(
            side=tk.LEFT, padx=8,
        )

        skip_row = tk.Frame(self._page_main, bg=self.BG)
        skip_row.pack(pady=(0, 2))
        self._make_btn(
            skip_row, s["skip"], self.skip,
            bg=self.BG, fg=self.FG_DIM, active_bg=self.BG, active_fg=self.FG,
        ).pack()

        self._build_pet()

        tk.Frame(self._page_main, height=1, bg=th["SEP"]).pack(
            fill=tk.X, padx=20, pady=(14, 0),
        )

        hdr = tk.Frame(self._page_main, bg=self.BG)
        hdr.pack(fill=tk.X, padx=20, pady=(10, 6))
        tk.Label(
            hdr, text=s["tasks_header"],
            font=("Segoe UI", 13, "bold"), bg=self.BG, fg=self.FG,
        ).pack(side=tk.LEFT)
        tk.Button(
            hdr, text=s["archive_btn"],
            font=("Segoe UI", 9), bg=self.BG, fg=self.FG_DIM,
            activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2",
            command=self._archive_done,
        ).pack(side=tk.RIGHT)

        input_row = tk.Frame(self._page_main, bg=self.BG)
        input_row.pack(fill=tk.X, padx=20, pady=(0, 8))
        self._entry = tk.Entry(
            input_row, font=("Segoe UI", 11),
            bg=self.BG3, fg=self.FG, insertbackground=self.FG,
            relief="flat", bd=0,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=7, padx=(0, 8))
        self._entry.bind("<Return>", lambda _e: self._add_task())
        self._add_btn = tk.Button(
            input_row, text="+",
            font=("Segoe UI", 14, "bold"),
            bg="#e74c3c", fg=self.FG, activebackground="#c0392b", activeforeground=self.FG,
            padx=12, pady=4, bd=0, relief="flat", cursor="hand2",
            command=self._add_task,
        )
        self._add_btn.pack(side=tk.LEFT)

        list_wrap = tk.Frame(self._page_main, bg=self.BG)
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))
        self._list_canvas = tk.Canvas(
            list_wrap, bg=self.BG, highlightthickness=0, height=160,
        )
        sb = tk.Scrollbar(list_wrap, orient="vertical", command=self._list_canvas.yview)
        self._task_frame = tk.Frame(self._list_canvas, bg=self.BG)
        self._task_win = self._list_canvas.create_window(
            (0, 0), window=self._task_frame, anchor="nw",
        )
        self._list_canvas.bind(
            "<Configure>",
            lambda e: self._list_canvas.itemconfig(self._task_win, width=e.width),
        )
        self._task_frame.bind(
            "<Configure>",
            lambda _e: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all"),
            ),
        )
        self._list_canvas.configure(yscrollcommand=sb.set)
        self._list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._list_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._list_canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

    # ──────────────────────────────────────────────── Archive page ──

    def _build_archive_page(self) -> None:
        s  = STRINGS[self._lang]
        th = THEMES[self._theme]
        self._page_archive = tk.Frame(self._content, bg=self.BG)

        hdr = tk.Frame(self._page_archive, bg=self.BG)
        hdr.pack(fill=tk.X, padx=20, pady=(16, 8))
        tk.Label(
            hdr, text=s["archive_title"],
            font=("Segoe UI", 14, "bold"), bg=self.BG, fg=self.FG,
        ).pack(side=tk.LEFT)
        tk.Button(
            hdr, text=s["delete_all"],
            font=("Segoe UI", 9), bg=self.BG, fg="#e74c3c",
            activebackground=self.BG, activeforeground="#c0392b",
            bd=0, relief="flat", cursor="hand2",
            command=self._clear_archive,
        ).pack(side=tk.RIGHT, pady=2)
        tk.Frame(self._page_archive, height=1, bg=th["SEP"]).pack(
            fill=tk.X, padx=20, pady=(0, 8),
        )

        list_wrap = tk.Frame(self._page_archive, bg=self.BG)
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))
        self._arc_canvas = tk.Canvas(list_wrap, bg=self.BG, highlightthickness=0)
        arc_sb = tk.Scrollbar(list_wrap, orient="vertical", command=self._arc_canvas.yview)
        self._arc_inner = tk.Frame(self._arc_canvas, bg=self.BG)
        self._arc_win_id = self._arc_canvas.create_window(
            (0, 0), window=self._arc_inner, anchor="nw",
        )
        self._arc_canvas.bind(
            "<Configure>",
            lambda e: self._arc_canvas.itemconfig(self._arc_win_id, width=e.width),
        )
        self._arc_inner.bind(
            "<Configure>",
            lambda _e: self._arc_canvas.configure(
                scrollregion=self._arc_canvas.bbox("all"),
            ),
        )
        self._arc_canvas.configure(yscrollcommand=arc_sb.set)
        self._arc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        arc_sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ──────────────────────────────────────────────── Settings page ──

    def _build_settings_page(self) -> None:
        self._page_settings = tk.Frame(self._content, bg=self.BG)

        wrap = tk.Frame(self._page_settings, bg=self.BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        self._settings_canvas = tk.Canvas(wrap, bg=self.BG, highlightthickness=0)
        settings_sb = tk.Scrollbar(
            wrap, orient="vertical", command=self._settings_canvas.yview,
        )
        self._settings_inner = tk.Frame(self._settings_canvas, bg=self.BG)
        self._settings_win_id = self._settings_canvas.create_window(
            (0, 0), window=self._settings_inner, anchor="nw",
        )
        self._settings_canvas.bind(
            "<Configure>",
            lambda e: self._settings_canvas.itemconfig(
                self._settings_win_id, width=e.width,
            ),
        )
        self._settings_inner.bind(
            "<Configure>",
            lambda _e: self._settings_canvas.configure(
                scrollregion=self._settings_canvas.bbox("all"),
            ),
        )
        self._settings_canvas.configure(yscrollcommand=settings_sb.set)
        self._settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settings_sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _populate_settings(self) -> None:
        s  = STRINGS[self._lang]
        th = THEMES[self._theme]
        inner = self._settings_inner
        self._color_btns = {}

        for w in inner.winfo_children():
            w.destroy()

        def section(title: str) -> None:
            tk.Label(
                inner, text=title,
                font=("Segoe UI", 11, "bold"), bg=self.BG, fg=self.FG,
            ).pack(pady=(14, 2), padx=20, anchor="w")
            tk.Frame(inner, height=1, bg=th["SEP"]).pack(fill=tk.X, padx=20, pady=(0, 4))

        # ── Pausenzeiten ──────────────────────────────────────────────────────
        section(s["break_times"])
        self._settings_fields: dict[str, tk.Entry] = {}
        for key, lk, color in (
            ("short_break", "short_min", "#27ae60"),
            ("long_break",  "long_min",  "#2980b9"),
        ):
            tk.Label(
                inner, text=s[lk], font=("Segoe UI", 10), bg=self.BG, fg=self.FG,
            ).pack(pady=(6, 2), padx=20, anchor="w")
            e = tk.Entry(
                inner, font=("Segoe UI", 13, "bold"),
                bg=self.BG3, fg=color, insertbackground=self.FG,
                justify="center", relief="flat", bd=0, width=8,
            )
            e.insert(0, str(self.MODES[key][2] // 60))
            e.pack(ipady=5, padx=20, anchor="w")
            self._settings_fields[key] = e
            e.bind("<Return>",   lambda _ev: self._settings_save())
            e.bind("<FocusOut>", lambda _ev: self._settings_save())

        # Break schedule
        tk.Frame(inner, height=1, bg=th["SEP"]).pack(fill=tk.X, padx=20, pady=(10, 0))
        tk.Label(
            inner, text=s["break_schedule"],
            font=("Segoe UI", 9), bg=self.BG, fg=self.FG_DIM,
        ).pack(pady=(6, 4))
        self._sched_frame = tk.Frame(inner, bg=self.BG)
        self._sched_frame.pack()
        self._sched_copy = self._break_schedule[:]
        self._sched_btns: list[tk.Button] = []

        def bc(bt: str) -> str:
            return "#27ae60" if bt == "short_break" else "#2980b9"

        def bl(i: int, bt: str) -> str:
            return ("🟢" if bt == "short_break" else "🔵") + f"\n{i + 1}"

        def toggle_cyc(i: int) -> None:
            self._sched_copy[i] = (
                "long_break" if self._sched_copy[i] == "short_break" else "short_break"
            )
            self._sched_btns[i].config(
                text=bl(i, self._sched_copy[i]),
                bg=bc(self._sched_copy[i]),
                activebackground=bc(self._sched_copy[i]),
            )
            self._break_schedule = self._sched_copy[:]
            self._save_config()

        for i, bt in enumerate(self._sched_copy):
            b = tk.Button(
                self._sched_frame, text=bl(i, bt),
                font=("Segoe UI", 9, "bold"),
                bg=bc(bt), fg=self.FG, activebackground=bc(bt), activeforeground=self.FG,
                width=4, pady=4, bd=0, relief="flat", cursor="hand2",
                command=lambda idx=i: toggle_cyc(idx),
            )
            b.pack(side=tk.LEFT, padx=3)
            self._sched_btns.append(b)

        # ── Farben ────────────────────────────────────────────────────────────
        section(s["colors_section"])
        for mode_key, lk in (
            ("work",        "color_work"),
            ("short_break", "color_short"),
            ("long_break",  "color_long"),
        ):
            row = tk.Frame(inner, bg=self.BG)
            row.pack(fill=tk.X, padx=20, pady=3)
            tk.Label(
                row, text=s[lk], font=("Segoe UI", 10),
                bg=self.BG, fg=self.FG, anchor="w", width=16,
            ).pack(side=tk.LEFT)
            _, color, _ = self.MODES[mode_key]
            cbtn = tk.Button(
                row, bg=color, width=4, height=1,
                relief="groove", bd=2, cursor="hand2",
                command=lambda k=mode_key: self._pick_color(k),
            )
            cbtn.pack(side=tk.LEFT, padx=(4, 0))
            self._color_btns[mode_key] = cbtn

        # ── Erscheinungsbild ──────────────────────────────────────────────────
        section(s["appearance"])
        app_row = tk.Frame(inner, bg=self.BG)
        app_row.pack(pady=(4, 2))
        for val, lk in (("dark", "dark_btn"), ("light", "light_btn")):
            active = self._theme == val
            tk.Button(
                app_row, text=s[lk],
                font=("Segoe UI", 10, "bold" if active else "normal"),
                bg=self.ACCENT_SEL if active else self.BG3,
                fg=self.FG if active else self.FG_DIM,
                activebackground=self.ACCENT_SEL, activeforeground=self.FG,
                padx=12, pady=6, bd=0, relief="flat", cursor="hand2",
                command=lambda v=val: self._set_theme(v),
            ).pack(side=tk.LEFT, padx=6)

        # ── Sprache ───────────────────────────────────────────────────────────
        section(s["language"])
        lang_row = tk.Frame(inner, bg=self.BG)
        lang_row.pack(pady=(4, 2))
        for val, label in (("de", "🇩🇪  Deutsch"), ("en", "🇬🇧  English")):
            active = self._lang == val
            tk.Button(
                lang_row, text=label,
                font=("Segoe UI", 10, "bold" if active else "normal"),
                bg=self.ACCENT_SEL if active else self.BG3,
                fg=self.FG if active else self.FG_DIM,
                activebackground=self.ACCENT_SEL, activeforeground=self.FG,
                padx=12, pady=6, bd=0, relief="flat", cursor="hand2",
                command=lambda v=val: self._set_lang(v),
            ).pack(side=tk.LEFT, padx=6)

        tk.Frame(inner, height=8, bg=self.BG).pack()

    def _settings_save(self) -> None:
        for key, entry in self._settings_fields.items():
            try:
                mins = int(entry.get().strip())
                if mins < 1:
                    raise ValueError
            except ValueError:
                entry.config(fg="#e74c3c")
                return
            label, clr, _ = self.MODES[key]
            self.MODES[key] = (label, clr, mins * 60)
            if self.mode == key:
                self.time_left = mins * 60
        self._break_schedule = self._sched_copy[:]
        self._save_config()
        self._refresh()

    def _pick_color(self, mode_key: str) -> None:
        s = STRINGS[self._lang]
        _, cur_color, _ = self.MODES[mode_key]
        result = colorchooser.askcolor(
            color=cur_color, title=s["choose_color"], parent=self.root,
        )
        if result[1]:
            new_color = result[1]
            label, _, time = self.MODES[mode_key]
            self.MODES[mode_key] = (label, new_color, time)
            if mode_key in self._color_btns:
                self._color_btns[mode_key].config(bg=new_color)
            self._save_config()
            self._refresh()

    def _set_theme(self, theme: str) -> None:
        if self._theme == theme:
            return
        self._theme = theme
        self._save_config()
        self._rebuild_ui()

    def _set_lang(self, lang: str) -> None:
        if self._lang == lang:
            return
        self._lang = lang
        self._save_config()
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        """Tear down and rebuild entire UI for theme or language changes."""
        self.running = False
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        if self._notif_job:
            self.root.after_cancel(self._notif_job)
            self._notif_job = None

        saved_todos    = [(v.get(), t) for v, r, t in self._todos if r.winfo_exists()]
        saved_archived = self._archived[:]
        saved_mode     = self.mode
        saved_time     = self.time_left
        saved_cycles   = self.cycles_done
        saved_muted    = self._muted
        saved_pet      = self._pet_type

        self._apply_theme_colors()
        self.root.configure(bg=self.BG)

        # Update MODES labels to new language
        s = STRINGS[self._lang]
        for key in ("work", "short_break", "long_break"):
            _, color, time = self.MODES[key]
            self.MODES[key] = (s[key], color, time)

        for child in self.root.winfo_children():
            child.destroy()

        self._todos        = []
        self._archived     = []
        self._menu_open    = False
        self._current_page = "main"
        self._notif_job    = None
        self._color_btns   = {}
        self.mode          = saved_mode
        self.time_left     = saved_time
        self.cycles_done   = saved_cycles
        self._muted        = saved_muted
        self._pet_type     = saved_pet

        self._build_ui()
        self._refresh()

        for done, text in saved_todos:
            self._add_task_internal(text, done)
        self._archived = saved_archived

        self._populate_settings()
        self._show_page("settings")

    # ──────────────────────────────────────────── Hamburger menu ──

    def _toggle_menu(self) -> None:
        self._close_menu() if self._menu_open else self._open_menu()

    def _open_menu(self) -> None:
        s = STRINGS[self._lang]
        self._menu_open = True
        self._mute_menu_btn.config(
            text=s["menu_muted"] if self._muted else s["menu_mute"],
        )
        self._menu_overlay.place(relx=1.0, x=-16, y=48, anchor="ne")
        self._menu_overlay.lift()

    def _close_menu(self) -> None:
        self._menu_open = False
        self._menu_overlay.place_forget()

    def _on_root_click(self, event: tk.Event) -> None:
        if not self._menu_open:
            return
        mx = self._menu_overlay.winfo_rootx()
        my = self._menu_overlay.winfo_rooty()
        mw = self._menu_overlay.winfo_width()
        mh = self._menu_overlay.winfo_height()
        if not (mx <= event.x_root <= mx + mw and my <= event.y_root <= my + mh):
            self._close_menu()

    def _menu_mute(self) -> None:
        self._muted = not self._muted
        self._close_menu()

    def _menu_settings(self) -> None:
        self._close_menu()
        self._populate_settings()
        self._show_page("settings")

    def _menu_archive(self) -> None:
        self._close_menu()
        self._render_archive_content()
        self._show_page("archive")

    # ──────────────────────────────────────────── Notification bar ──

    def _show_notif(self, message: str, color: str) -> None:
        if self._notif_job:
            self.root.after_cancel(self._notif_job)
            self._notif_job = None
        bg_map = {"#e74c3c": "#3a2020", "#27ae60": "#203a28", "#2980b9": "#1a2c3a"}
        bg = bg_map.get(color, self.BG2)
        self._notif_frame.config(bg=bg)
        self._notif_label.config(text=message, bg=bg)
        self._notif_btn.config(bg=color, activebackground=color)
        self._notif_frame.pack(fill=tk.X, after=self._header_frame)
        self._notif_job = self.root.after(6000, self._notif_ok)

    def _notif_ok(self) -> None:
        if self._notif_job:
            self.root.after_cancel(self._notif_job)
            self._notif_job = None
        self._notif_frame.pack_forget()
        if not self.running:
            self.toggle()

    # ──────────────────────────────────────────── Helpers ──

    def _make_btn(
        self, parent, text, cmd,
        bg=None, fg="#ffffff", active_bg=None, active_fg="#ffffff", width=None,
    ) -> tk.Button:
        _, color, _ = self.MODES[self.mode]
        bg = bg or color
        active_bg = active_bg or color
        kw = dict(
            text=text, font=("Segoe UI", 11, "bold"),
            bg=bg, fg=fg, activebackground=active_bg, activeforeground=active_fg,
            padx=14, pady=8, bd=0, relief="flat", cursor="hand2", command=cmd,
        )
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    # ──────────────────────────────────────────── Pet ──

    def _build_pet(self) -> None:
        s = STRINGS[self._lang]
        pet_lbl = "🐱  " + ("Katze" if self._lang == "de" else "Cat") if self._pet_type == "cat" \
             else "🐶  " + ("Hund"  if self._lang == "de" else "Dog")
        pet_wrap = tk.Frame(self._page_main, bg=self.BG)
        pet_wrap.pack(pady=(2, 0))
        self._pet_canvas = tk.Canvas(
            pet_wrap, width=90, height=90,
            bg=self.BG, highlightthickness=0, cursor="hand2",
        )
        self._pet_canvas.pack()
        self._pet_canvas.bind("<Button-1>", lambda _e: self._toggle_pet())
        self._pet_lbl = tk.Label(
            pet_wrap, text=pet_lbl, font=("Segoe UI", 10),
            bg=self.BG, fg=self.FG_DIM, cursor="hand2",
        )
        self._pet_lbl.pack()
        self._pet_lbl.bind("<Button-1>", lambda _e: self._toggle_pet())
        self._pet_tick()

    def _toggle_pet(self) -> None:
        self._pet_type = "dog" if self._pet_type == "cat" else "cat"
        pet_lbl = "🐱  " + ("Katze" if self._lang == "de" else "Cat") if self._pet_type == "cat" \
             else "🐶  " + ("Hund"  if self._lang == "de" else "Dog")
        try:
            self._pet_lbl.config(text=pet_lbl)
        except Exception:
            pass
        self._save_config()

    def _pet_state(self) -> str:
        if self.mode != "work":
            return "sleep"
        return "play" if self.running else "idle"

    def _pet_tick(self) -> None:
        try:
            if not self._pet_canvas.winfo_exists():
                return
        except Exception:
            return
        t = _time_mod.time() * 1000
        self._draw_pet(t)
        self.root.after(50, self._pet_tick)

    def _draw_pet(self, t: float) -> None:
        c = self._pet_canvas
        c.delete("pet")
        ps = self._pet_state()
        if self._pet_type == "cat":
            self._draw_cat(c, t, ps)
        else:
            self._draw_dog(c, t, ps)

    # ── bezier helper for tails ──
    @staticmethod
    def _bezier_pts(x0, y0, cx1, cy1, cx2, cy2, x1, y1, steps=18):
        pts = []
        for i in range(steps + 1):
            s = i / steps
            bx = (1-s)**3*x0 + 3*(1-s)**2*s*cx1 + 3*(1-s)*s**2*cx2 + s**3*x1
            by = (1-s)**3*y0 + 3*(1-s)**2*s*cy1 + 3*(1-s)*s**2*cy2 + s**3*y1
            pts += [bx, by]
        return pts

    def _draw_cat(self, c: tk.Canvas, t: float, ps: str) -> None:
        F, D, P, cx = "#8888aa", "#56567a", "#e088a0", 45

        if ps == "sleep":
            c.create_oval(28, 59, 72, 81, fill=F, outline="", tags="pet")
            tail = self._bezier_pts(70,65, 83,52, 80,74, 68,72)
            c.create_line(*tail, fill=F, width=5, smooth=True, capstyle="round", tags="pet")
            c.create_oval(13, 54, 37, 78, fill=F, outline="", tags="pet")
            c.create_polygon(17,58, 19,48, 25,57, fill=F, outline="", tags="pet")
            c.create_polygon(18,57, 20,52, 24,57, fill=P, outline="", tags="pet")
            c.create_arc(18,63, 24,69, start=0, extent=180, style="arc", outline=D, width=2, tags="pet")
            c.create_arc(26,63, 32,69, start=0, extent=180, style="arc", outline=D, width=2, tags="pet")
            zy = 18 - (t % 2400) / 2400 * 12
            if (t % 2400) / 300 > 0.5:
                c.create_text(55, zy+28, text="z", font=("Segoe UI", 9,  "bold"), fill=D, tags="pet")
                c.create_text(61, zy+16, text="z", font=("Segoe UI", 11, "bold"), fill=D, tags="pet")
                c.create_text(68, zy+2,  text="Z", font=("Segoe UI", 13, "bold"), fill=D, tags="pet")
            return

        bou = -abs(math.sin(t * .007)) * 10 if ps == "play" else 0
        br  = math.sin(t * .0018) * 1.4
        ta  = math.sin(t * .0012) * (.68 if ps == "play" else .28)
        blk = (t % 3800) < 160
        fy, hy = 83 + bou, 83 + bou - 37

        # tail
        ty3 = fy - 62 if ps == "play" else fy - 55
        tail = self._bezier_pts(cx+16,fy-14, cx+38+ta*8,fy-32, cx+34+ta*8,fy-50, cx+22+ta*8,ty3)
        c.create_line(*tail, fill=F, width=5, smooth=True, capstyle="round", tags="pet")
        # body
        by = fy - 15; bry = 11 + br * .5
        c.create_oval(cx-16, by-bry, cx+16, by+bry, fill=F, outline="", tags="pet")
        # head
        c.create_oval(cx-13, hy-13, cx+13, hy+13, fill=F, outline="", tags="pet")
        # ears
        eh = 19 if ps == "play" else 17
        c.create_polygon(cx-14,hy-5, cx-10,hy-eh, cx-3,hy-7,  fill=F, outline="", tags="pet")
        c.create_polygon(cx+3, hy-7, cx+10,hy-eh, cx+14,hy-5, fill=F, outline="", tags="pet")
        c.create_polygon(cx-12,hy-6, cx-9,hy-eh+4, cx-5,hy-7,  fill=P, outline="", tags="pet")
        c.create_polygon(cx+5, hy-7, cx+9,hy-eh+4, cx+12,hy-6, fill=P, outline="", tags="pet")
        # eyes
        eo = 3.5 if ps == "play" else (.5 if blk else 2.8)
        c.create_oval(cx-7.5, hy-eo, cx-2.5, hy+eo, fill=D, outline="", tags="pet")
        c.create_oval(cx+2.5, hy-eo, cx+7.5, hy+eo, fill=D, outline="", tags="pet")
        if not blk:
            c.create_oval(cx-5,.9, cx-3,.9+1.8, fill="#ffffff", outline="", tags="pet")  # shine dots
            c.create_oval(cx-5,hy-2, cx-3,hy,   fill="#ffffff", outline="", tags="pet")
            c.create_oval(cx+5,hy-2, cx+7,hy,   fill="#ffffff", outline="", tags="pet")
        # nose
        c.create_polygon(cx-2,hy+5, cx+2,hy+5, cx,hy+7, fill=P, outline="", tags="pet")
        # paws
        if ps == "play":
            c.create_oval(cx-17,fy-2, cx-5,fy+6,  fill=F, outline="", tags="pet")
            c.create_oval(cx+5, fy-2, cx+17,fy+6, fill=F, outline="", tags="pet")
        else:
            c.create_oval(cx-16,fy-5, cx-2,fy+4,  fill=F, outline="", tags="pet")
            c.create_oval(cx+2, fy-5, cx+16,fy+4, fill=F, outline="", tags="pet")

    def _draw_dog(self, c: tk.Canvas, t: float, ps: str) -> None:
        F, D, SN, cx = "#c8966e", "#7a4e28", "#d4a880", 45

        if ps == "sleep":
            c.create_oval(28, 59, 72, 81, fill=F, outline="", tags="pet")
            tail = self._bezier_pts(70,64, 80,54, 78,72, 67,72)
            c.create_line(*tail, fill=F, width=6, smooth=True, capstyle="round", tags="pet")
            c.create_oval(12, 53, 38, 79, fill=F, outline="", tags="pet")
            c.create_oval(10, 62, 22, 82, fill=F, outline="", tags="pet")   # floppy ear
            c.create_oval(14, 64, 26, 72, fill=SN, outline="", tags="pet")  # snout
            c.create_oval(15, 65, 21, 69, fill=D,  outline="", tags="pet")  # nose
            c.create_arc(19,60, 25,66, start=0, extent=180, style="arc", outline=D, width=2, tags="pet")
            c.create_arc(27,60, 33,66, start=0, extent=180, style="arc", outline=D, width=2, tags="pet")
            zy = 18 - (t % 2400) / 2400 * 12
            if (t % 2400) / 300 > 0.5:
                c.create_text(55, zy+28, text="z", font=("Segoe UI", 9,  "bold"), fill=D, tags="pet")
                c.create_text(61, zy+16, text="z", font=("Segoe UI", 11, "bold"), fill=D, tags="pet")
                c.create_text(68, zy+2,  text="Z", font=("Segoe UI", 13, "bold"), fill=D, tags="pet")
            return

        bou = -abs(math.sin(t * .007)) * 10 if ps == "play" else 0
        br  = math.sin(t * .0018) * 1.4
        tsp = .012 if ps == "play" else .006
        ta  = math.sin(t * tsp) * (1.1 if ps == "play" else .44)
        blk = (t % 4000) < 180
        fy, hy = 83 + bou, 83 + bou - 38

        # tail
        tail = self._bezier_pts(cx+17,fy-16, cx+28+ta*10,fy-28, cx+26+ta*10,fy-40, cx+18+ta*8,fy-42)
        c.create_line(*tail, fill=F, width=6, smooth=True, capstyle="round", tags="pet")
        # body
        bry = 12 + br * .5
        c.create_oval(cx-17, fy-16-bry, cx+17, fy-16+bry, fill=F, outline="", tags="pet")
        # head
        c.create_oval(cx-15, hy-15, cx+15, hy+15, fill=F, outline="", tags="pet")
        # floppy ears (drawn on top of head sides)
        c.create_oval(cx-25, hy-6, cx-11, hy+16, fill=F, outline="", tags="pet")
        c.create_oval(cx+11, hy-6, cx+25, hy+16, fill=F, outline="", tags="pet")
        # snout
        c.create_oval(cx-7, hy+1, cx+7, hy+11, fill=SN, outline="", tags="pet")
        # eyes
        eo = 4 if ps == "play" else (.5 if blk else 3.5)
        c.create_oval(cx-9, hy-3-eo, cx-3, hy-3+eo, fill=D, outline="", tags="pet")
        c.create_oval(cx+3, hy-3-eo, cx+9, hy-3+eo, fill=D, outline="", tags="pet")
        if not blk:
            c.create_oval(cx-6,hy-5, cx-4,hy-3, fill="#ffffff", outline="", tags="pet")
            c.create_oval(cx+6,hy-5, cx+8,hy-3, fill="#ffffff", outline="", tags="pet")
        # nose
        c.create_oval(cx-3.5, hy+1.5, cx+3.5, hy+6.5, fill=D, outline="", tags="pet")
        # paws
        if ps == "play":
            c.create_oval(cx-19,fy-1, cx-5,fy+7,  fill=F, outline="", tags="pet")
            c.create_oval(cx+5, fy-1, cx+19,fy+7, fill=F, outline="", tags="pet")
        else:
            c.create_oval(cx-17,fy-4, cx-3,fy+6,  fill=F, outline="", tags="pet")
            c.create_oval(cx+3, fy-4, cx+17,fy+6, fill=F, outline="", tags="pet")

    # ──────────────────────────────────────────── Task logic ──

    def _add_task(self) -> None:
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, tk.END)
        self._add_task_internal(text, False)

    def _add_task_internal(self, text: str, done: bool = False) -> None:
        th = THEMES[self._theme]
        done_var = tk.BooleanVar(value=False)
        row = tk.Frame(self._task_frame, bg=self.BG)
        row.pack(fill=tk.X, pady=3)

        arc_btn = tk.Button(
            row, text="→", font=("Segoe UI", 11),
            bg=self.BG, fg="#555555",
            activebackground=self.BG, activeforeground="#27ae60",
            bd=0, relief="flat", state="disabled",
            command=lambda r=row, t=text: self._archive_single(r, t),
        )
        cb = tk.Checkbutton(
            row, variable=done_var,
            bg=self.BG, activebackground=self.BG,
            selectcolor=th["SEL_CHK"],
            bd=0, relief="flat", cursor="hand2",
            command=lambda: self._toggle_done(lbl, done_var, arc_btn),
        )
        cb.pack(side=tk.LEFT)
        lbl = tk.Label(
            row, text=text, font=("Segoe UI", 11),
            bg=self.BG, fg=self.FG, anchor="w",
        )
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(
            row, text="×", font=("Segoe UI", 12),
            bg=self.BG, fg=self.FG_DIM,
            activebackground=self.BG, activeforeground=self.FG,
            bd=0, relief="flat", cursor="hand2",
            command=lambda r=row: self._remove_task(r),
        ).pack(side=tk.RIGHT)
        arc_btn.pack(side=tk.RIGHT, padx=(0, 4))
        self._todos.append((done_var, row, text))

        if done:
            done_var.set(True)
            self._toggle_done(lbl, done_var, arc_btn)

    def _toggle_done(self, lbl: tk.Label, var: tk.BooleanVar, arc_btn: tk.Button) -> None:
        if var.get():
            lbl.config(fg=self.FG_DIM, font=("Segoe UI", 11, "overstrike"))
            arc_btn.config(state="normal", cursor="hand2", fg=self.FG_DIM)
        else:
            lbl.config(fg=self.FG, font=("Segoe UI", 11))
            arc_btn.config(state="disabled", cursor="arrow", fg="#555555")

    def _remove_task(self, row: tk.Frame) -> None:
        row.destroy()
        self._todos = [(v, r, t) for v, r, t in self._todos if r.winfo_exists()]

    def _archive_single(self, row: tk.Frame, text: str) -> None:
        self._archived.append(text)
        row.destroy()
        self._todos = [(v, r, t) for v, r, t in self._todos if r.winfo_exists()]

    def _archive_done(self) -> None:
        remaining = []
        for var, row, text in self._todos:
            if var.get() and row.winfo_exists():
                self._archived.append(text)
                row.destroy()
            else:
                remaining.append((var, row, text))
        self._todos = remaining

    # ──────────────────────────────────────────── Archive page ──

    def _render_archive_content(self) -> None:
        s = STRINGS[self._lang]
        for w in self._arc_inner.winfo_children():
            w.destroy()
        if not self._archived:
            tk.Label(
                self._arc_inner, text=s["no_archived"],
                font=("Segoe UI", 11), bg=self.BG, fg=self.FG_DIM,
            ).pack(pady=20)
            return
        for i, text in enumerate(self._archived):
            row = tk.Frame(self._arc_inner, bg=self.BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(
                row, text="✓", font=("Segoe UI", 10), bg=self.BG, fg="#27ae60",
            ).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(
                row, text=text, font=("Segoe UI", 11, "overstrike"),
                bg=self.BG, fg=self.FG_DIM, anchor="w",
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(
                row, text="×", font=("Segoe UI", 12),
                bg=self.BG, fg="#555555",
                activebackground=self.BG, activeforeground=self.FG,
                bd=0, relief="flat", cursor="hand2",
                command=lambda idx=i: self._remove_archived(idx),
            ).pack(side=tk.RIGHT)

    def _remove_archived(self, index: int) -> None:
        if 0 <= index < len(self._archived):
            self._archived.pop(index)
        self._render_archive_content()

    def _clear_archive(self) -> None:
        self._archived.clear()
        self._render_archive_content()

    # ──────────────────────────────────────────── Timer ──

    def toggle(self) -> None:
        s = STRINGS[self._lang]
        if self.running:
            self.running = False
            self.start_btn.config(text=s["resume"])
            if self._job:
                self.root.after_cancel(self._job)
        else:
            self.running = True
            self.start_btn.config(text=s["pause"])
            self._tick()

    def _tick(self) -> None:
        if not self.running:
            return
        if self.time_left > 0:
            self.time_left -= 1
            self._refresh()
            self._job = self.root.after(1000, self._tick)
        else:
            self.running = False
            self._session_done()

    def _session_done(self) -> None:
        s = STRINGS[self._lang]
        threading.Thread(target=self._beep, daemon=True).start()
        if self.mode == "work":
            self.cycles_done += 1
            idx = self.cycles_done - 1
            break_type = (
                self._break_schedule[idx]
                if idx < len(self._break_schedule) else "long_break"
            )
            self.mode = break_type
            msg = s["done_long"] if break_type == "long_break" else s["done_short"]
            if self.cycles_done >= self.cycles_max:
                self.cycles_done = 0
        else:
            self.mode = "work"
            msg = s["done_work"]
        self.time_left = self.MODES[self.mode][2]
        self.start_btn.config(text=s["start"])
        self._refresh()
        self._notify(msg)

    def reset(self) -> None:
        s = STRINGS[self._lang]
        self.running = False
        if self._job:
            self.root.after_cancel(self._job)
        self.time_left = self.MODES[self.mode][2]
        self.start_btn.config(text=s["start"])
        self._refresh()

    def skip(self) -> None:
        self.running = False
        if self._job:
            self.root.after_cancel(self._job)
        self.time_left = 0
        self._session_done()

    # ──────────────────────────────────────────── Time editing ──

    def _edit_time(self) -> None:
        if self.running:
            return
        _, color, current = self.MODES[self.mode]
        _closed = [False]

        entry = tk.Entry(
            self.canvas, font=("Segoe UI", 32, "bold"),
            bg=self.BG2, fg=color, insertbackground=color,
            justify="center", relief="flat", bd=0, width=5,
        )
        entry.insert(0, str(current // 60))
        entry.select_range(0, tk.END)
        entry_win = self.canvas.create_window(110, 110, window=entry, anchor="center")

        def close(_e=None) -> None:
            if _closed[0]:
                return
            _closed[0] = True
            try:
                self.canvas.delete(entry_win)
                entry.destroy()
            except Exception:
                pass

        def confirm(_e=None) -> None:
            try:
                mins = int(entry.get().strip())
                if mins < 1:
                    raise ValueError
            except ValueError:
                entry.config(fg="#e74c3c")
                return
            label, clr, _ = self.MODES[self.mode]
            self.MODES[self.mode] = (label, clr, mins * 60)
            self.time_left = mins * 60
            self._save_config()
            self._refresh()
            close()

        entry.bind("<Return>", confirm)
        entry.bind("<Escape>", close)
        entry.bind("<FocusOut>", close)
        entry.focus_set()

    def _adjust_cycles(self, delta: int) -> None:
        new_val = self.cycles_max + delta
        if not (2 <= new_val <= 8):
            return
        old = self._break_schedule[:]
        self.cycles_max = new_val
        if new_val > len(old):
            self._break_schedule = old + ["short_break"] * (new_val - len(old))
        else:
            self._break_schedule = old[:new_val]
        if self.cycles_done >= self.cycles_max:
            self.cycles_done = 0
        self._minus_btn.config(fg=self.FG_DIM if self.cycles_max > 2 else "#444444")
        self._plus_btn.config(fg=self.FG_DIM if self.cycles_max < 8 else "#444444")
        self._save_config()
        self._refresh()

    # ──────────────────────────────────────────── Config ──

    @staticmethod
    def _config_path() -> pathlib.Path:
        if getattr(sys, "frozen", False):
            return pathlib.Path(sys.executable).parent / "pomodoro_config.json"
        return pathlib.Path(__file__).parent / "pomodoro_config.json"

    def _load_config(self) -> None:
        try:
            data = json.loads(self._config_path().read_text())
            for key in ("work", "short_break", "long_break"):
                if key in data:
                    label, color, _ = self.MODES[key]
                    self.MODES[key] = (label, color, int(data[key]) * 60)
            if "cycles_max" in data:
                self.cycles_max = max(2, min(8, int(data["cycles_max"])))
                self._break_schedule = (
                    ["short_break"] * (self.cycles_max - 1) + ["long_break"]
                )
            if "break_schedule" in data:
                loaded = data["break_schedule"]
                if (isinstance(loaded, list)
                        and len(loaded) == self.cycles_max
                        and all(b in ("short_break", "long_break") for b in loaded)):
                    self._break_schedule = loaded
            if "lang" in data and data["lang"] in ("de", "en"):
                self._lang = data["lang"]
            if "theme" in data and data["theme"] in ("dark", "light"):
                self._theme = data["theme"]
            if "pet_type" in data and data["pet_type"] in ("cat", "dog"):
                self._pet_type = data["pet_type"]
            for key in ("work", "short_break", "long_break"):
                ck = f"color_{key}"
                if ck in data and isinstance(data[ck], str) and data[ck].startswith("#"):
                    label, _, time = self.MODES[key]
                    self.MODES[key] = (label, data[ck], time)
        except Exception:
            pass

    def _save_config(self) -> None:
        try:
            data = {k: v[2] // 60 for k, v in self.MODES.items()}
            data["cycles_max"]     = self.cycles_max
            data["break_schedule"] = self._break_schedule
            data["lang"]           = self._lang
            data["theme"]          = self._theme
            data["pet_type"]       = self._pet_type
            for key in ("work", "short_break", "long_break"):
                data[f"color_{key}"] = self.MODES[key][1]
            self._config_path().write_text(json.dumps(data))
        except Exception:
            pass

    # ──────────────────────────────────────────── Display ──

    def _refresh(self) -> None:
        label, color, total = self.MODES[self.mode]
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        progress = self.time_left / total
        self.canvas.itemconfig(self._arc, extent=359.99 * progress, outline=color)
        self.canvas.itemconfig(self._time_text, text=time_str, fill=self.FG)
        self.mode_label.config(text=label)
        dots = "●" * self.cycles_done + "○" * (self.cycles_max - self.cycles_done)
        self.dots_label.config(text=dots, fg=color)
        self.start_btn.config(bg=color, activebackground=color)
        self._add_btn.config(bg=color, activebackground=color)
        self.root.title(f"{time_str}  –  {label}")

    def _beep(self) -> None:
        if self._muted:
            return
        try:
            if sys.platform == "win32":
                import winsound
                for freq, dur in [(880, 220), (660, 180), (880, 280)]:
                    winsound.Beep(freq, dur)
            else:
                # Cross-platform: generate sine-wave WAV and play via afplay (macOS) or aplay (Linux)
                sample_rate = 44100
                for freq, dur in [(880, 220), (660, 180), (880, 280)]:
                    n = int(sample_rate * dur / 1000)
                    data = struct.pack(
                        f"<{n}h",
                        *[int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
                          for i in range(n)]
                    )
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        tmp = f.name
                    with wave.open(tmp, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(data)
                    player = "afplay" if sys.platform == "darwin" else "aplay"
                    subprocess.run([player, tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.unlink(tmp)
        except Exception:
            pass

    def _notify(self, message: str) -> None:
        _, color, _ = self.MODES[self.mode]
        if self._current_page != "main":
            self._show_page("main")
        self._show_notif(message, color)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "pomodoro.timer.1.0"
        )
    except Exception:
        pass

    root = tk.Tk()
    _meipass = getattr(sys, "_MEIPASS", None)
    _icon = (
        pathlib.Path(_meipass) / "pomodoro_timer.ico"
        if _meipass
        else pathlib.Path(__file__).parent / "pomodoro_timer.ico"
    )
    try:
        root.iconbitmap(str(_icon))
    except Exception:
        pass

    app = PomodoroApp(root)
    root.mainloop()
