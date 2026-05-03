import tkinter as tk
from tkinter import ttk

try:
    from win10toast import ToastNotifier
except Exception:
    ToastNotifier = None


class Notifier:
    def __init__(self, root=None):
        self._impl = None
        self.root = root
        if ToastNotifier:
            try:
                self._impl = ToastNotifier()
            except Exception:
                self._impl = None

    def notify(self, title, msg, on_take=None, on_ignore=None):
        # Show system toast if available
        if self._impl:
            try:
                self._impl.show_toast(title, msg, duration=6, threaded=True)
            except Exception:
                pass

        # Also show an actionable small Tk window so user can click buttons.
        # Schedule UI creation on the Tk main thread via `after` to avoid
        # creating widgets from a background thread.
        try:
            if self.root:
                self.root.after(0, lambda: self._show_action_window(title, msg, on_take, on_ignore))
                return
        except Exception:
            pass

        # fallback to console
        print(f"NOTIFICATION: {title} - {msg}")

    def _show_action_window(self, title, msg, on_take, on_ignore):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.attributes('-topmost', True)
        # small no-resize window
        win.resizable(False, False)
        # make window appear above even if app is minimized
        try:
            win.attributes('-toolwindow', True)
        except Exception:
            pass

        lbl = ttk.Label(win, text=msg, padding=8)
        lbl.pack(padx=12, pady=8)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(padx=8, pady=8)

        def _take():
            try:
                if on_take:
                    on_take()
            finally:
                win.destroy()

        def _ignore():
            try:
                if on_ignore:
                    on_ignore()
            finally:
                win.destroy()

        take_btn = ttk.Button(btn_frame, text='Take break', command=_take)
        ignore_btn = ttk.Button(btn_frame, text='Ignore', command=_ignore)
        take_btn.pack(side='left', padx=6)
        ignore_btn.pack(side='left', padx=6)

        # place near bottom-right of screen
        try:
            win.update_idletasks()
            w = win.winfo_width()
            h = win.winfo_height()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = sw - w - 40
            y = sh - h - 80
            win.geometry(f'+{x}+{y}')
        except Exception:
            pass
