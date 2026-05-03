# MicroBreak — Intelligent Micro Breaks (Tkinter prototype)

Features:
- Sidebar with Home / Dashboard / Exercises
- Monitors active window title and mouse movement (Windows)
- Suggests breaks after long continuous activity and sends toast notifications
- Exercises with timers and simple animated progress
- Saves simple per-day stats to `~/.microbreak_data.json`

Requirements:
- Python 3.8+
- Install dependencies:

```powershell
pip install -r requirements.txt
```

Run:

```powershell
python main.py
```

Notes:
- This is a lightweight prototype. On Windows it uses Win32 APIs via ctypes and `win10toast` for notifications.
- For cross-platform support, enhancements and improved activity detection (keyboard, processes), add `psutil` and platform-specific code.
