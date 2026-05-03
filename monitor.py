import threading
import time
import json
import os
from datetime import datetime

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

class ActivityMonitor:
    def __init__(self, on_break_suggested=None, stats_path=None,
                 session_limit_seconds=50*60):
        self.on_break_suggested = on_break_suggested
        self.stats_path = stats_path or os.path.join(os.path.expanduser('~'), '.microbreak_data.json')
        self.session_limit = session_limit_seconds

        self.running = False
        self._thread = None

        self._last_mouse = None
        self._active_session = 0
        self._current_app = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=0.5)

    def _get_active_window_title(self):
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def _get_mouse_pos(self):
        class POINT(ctypes.Structure):
            _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _save_stats(self, app_name, seconds):
        today = datetime.now().strftime('%Y-%m-%d')
        data = {}
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}

        day = data.setdefault(today, {'apps': {}, 'exercises': []})
        day['apps'][app_name] = day['apps'].get(app_name, 0) + seconds

        with open(self.stats_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _run(self):
        self._last_mouse = self._get_mouse_pos()
        idle_start = None
        while self.running:
            try:
                title = self._get_active_window_title() or 'Unknown'
                mouse = self._get_mouse_pos()

                moved = mouse != self._last_mouse
                self._last_mouse = mouse

                if moved:
                    self._active_session += 1
                else:
                    # small decay when not moving
                    self._active_session += 0

                # track per-second usage for active window
                self._save_stats(title, 1)

                if self._active_session >= self.session_limit:
                    # trigger suggestion and reset session counter
                    if self.on_break_suggested:
                        self.on_break_suggested('You have been active for a long time')
                    self._active_session = 0

                time.sleep(1)
            except Exception:
                time.sleep(1)
