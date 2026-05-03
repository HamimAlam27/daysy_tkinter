import threading
import time
import tkinter as tk
from tkinter import ttk
import os
import json
from datetime import datetime

from monitor import ActivityMonitor
from exercises import ExercisesFrame
from dashboard import DashboardFrame
from notifications import Notifier

APP_DATA = os.path.join(os.path.expanduser('~'), '.microbreak_data.json')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MicroBreak — Intelligent Breaks')
        self.geometry('900x600')
        self.configure(bg='#1f2430')

        self.notifier = Notifier(self)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('Sidebar.TFrame', background='#111217')
        self.style.configure('Main.TFrame', background='#151722')
        self.style.configure('TButton', padding=6)

        self._create_layout()

        # session_limit_seconds set to 10s for testing break suggestion
        self.monitor = ActivityMonitor(on_break_suggested=self._on_break_suggested,
                           stats_path=APP_DATA,
                           session_limit_seconds=10)
        self.monitor_thread = None

    def _create_layout(self):
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True)

        sidebar = ttk.Frame(container, width=220, style='Sidebar.TFrame')
        sidebar.pack(side='left', fill='y')

        self.main = ttk.Frame(container, style='Main.TFrame')
        self.main.pack(side='right', fill='both', expand=True)

        # Sidebar buttons
        btn_home = ttk.Button(sidebar, text='Home', command=self.show_home)
        btn_dash = ttk.Button(sidebar, text='Dashboard', command=self.show_dashboard)
        btn_ex = ttk.Button(sidebar, text='Exercises', command=self.show_exercises)
        btn_quit = ttk.Button(sidebar, text='Quit', command=self.destroy)

        for b in (btn_home, btn_dash, btn_ex, btn_quit):
            b.pack(fill='x', padx=12, pady=8)

        # Pages
        self.pages = {}
        self.pages['home'] = self._build_home(self.main)
        self.pages['dashboard'] = DashboardFrame(self.main, data_path=APP_DATA)
        self.pages['exercises'] = ExercisesFrame(self.main, on_complete=self._exercise_complete)

        self.show_home()

    def _build_home(self, parent):
        f = ttk.Frame(parent)
        lbl = ttk.Label(f, text='Welcome to MicroBreak', font=('Segoe UI', 18))
        lbl.pack(pady=20)

        self.status_var = tk.StringVar(value='Monitor stopped')
        status = ttk.Label(f, textvariable=self.status_var)
        status.pack(pady=6)

        self.start_btn = ttk.Button(f, text='Start Monitor', command=self.toggle_monitor)
        self.start_btn.pack(pady=10)

        self.elapsed_var = tk.StringVar(value='Elapsed: 0s')
        elapsed_lbl = ttk.Label(f, textvariable=self.elapsed_var)
        elapsed_lbl.pack(pady=6)

        # Ignored breaks counter
        self.ignored_var = tk.IntVar(value=0)
        ignored_lbl = ttk.Label(f, textvariable=tk.StringVar(value='Ignored breaks: 0'))
        # create a dynamic label that reads from ignored_var
        def _ignored_text():
            return f'Ignored breaks: {self.ignored_var.get()}'
        self._ignored_label_var = tk.StringVar(value=_ignored_text())
        ignored_lbl = ttk.Label(f, textvariable=self._ignored_label_var)
        ignored_lbl.pack(pady=6)

        # load initial ignored count
        self._load_ignored_count()

        self._start_time = None

        return f

    def show_home(self):
        self._show_page('home')

    def show_dashboard(self):
        self.pages['dashboard'].refresh()
        self._show_page('dashboard')

    def show_exercises(self):
        self._show_page('exercises')

    def _show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        page = self.pages[name]
        page.pack(fill='both', expand=True)

    def toggle_monitor(self):
        if self.monitor.running:
            self.monitor.stop()
            self.start_btn.config(text='Start Monitor')
            self.status_var.set('Monitor stopped')
            self._start_time = None
        else:
            self.monitor.start()
            self.start_btn.config(text='Stop Monitor')
            self.status_var.set('Monitor running')
            self._start_time = time.time()
            self._update_elapsed()

    def _on_break_suggested(self, reason):
        # show notification and open Exercises page
        # show actionable notification with two buttons
        self.notifier.notify('Time for a break', reason,
                     on_take=self._show_and_open_exercises,
                     on_ignore=self._on_ignore)
        # keep behavior: also open exercises when suggested
        self.show_exercises()

    def _show_and_open_exercises(self):
        try:
            # if minimized/iconified, restore
            if str(self.state()) == 'iconic':
                self.deiconify()
            # bring to front
            self.lift()
            self.focus_force()
            # briefly set topmost to ensure visibility on Windows
            try:
                self.attributes('-topmost', True)
                self.after(200, lambda: self.attributes('-topmost', False))
            except Exception:
                pass
        except Exception:
            pass
        self.show_exercises()

    def _on_ignore(self):
        # increment ignored counter for today and update UI
        try:
            data = {}
            if os.path.exists(APP_DATA):
                with open(APP_DATA, 'r', encoding='utf-8') as f:
                    data = json.load(f)
        except Exception:
            data = {}

        today = datetime.now().strftime('%Y-%m-%d')
        day = data.setdefault(today, {'apps': {}, 'exercises': [], 'ignored': 0})
        day['ignored'] = day.get('ignored', 0) + 1

        try:
            with open(APP_DATA, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

        # update UI
        self.ignored_var.set(day['ignored'])
        self._ignored_label_var.set(f'Ignored breaks: {self.ignored_var.get()}')

    def _load_ignored_count(self):
        try:
            if not os.path.exists(APP_DATA):
                self.ignored_var.set(0)
                self._ignored_label_var.set('Ignored breaks: 0')
                return
            with open(APP_DATA, 'r', encoding='utf-8') as f:
                data = json.load(f)
            today = datetime.now().strftime('%Y-%m-%d')
            day = data.get(today, {})
            ignored = int(day.get('ignored', 0))
            self.ignored_var.set(ignored)
            self._ignored_label_var.set(f'Ignored breaks: {ignored}')
        except Exception:
            self.ignored_var.set(0)
            self._ignored_label_var.set('Ignored breaks: 0')

    def _exercise_complete(self, exercise_name):
        # Called when an exercise finishes
        self.notifier.notify('Exercise complete', exercise_name)
        # update dashboard
        self.pages['dashboard'].refresh()

    def _update_elapsed(self):
        if not self.monitor.running or not self._start_time:
            self.elapsed_var.set('Elapsed: 0s')
            return
        elapsed = int(time.time() - self._start_time)
        self.elapsed_var.set(f'Elapsed: {elapsed}s')
        self.after(1000, self._update_elapsed)


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
