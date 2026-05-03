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

        self.notifier = Notifier()

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('Sidebar.TFrame', background='#111217')
        self.style.configure('Main.TFrame', background='#151722')
        self.style.configure('TButton', padding=6)

        self._create_layout()

        self.monitor = ActivityMonitor(on_break_suggested=self._on_break_suggested,
                                       stats_path=APP_DATA)
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
        else:
            self.monitor.start()
            self.start_btn.config(text='Stop Monitor')
            self.status_var.set('Monitor running')

    def _on_break_suggested(self, reason):
        # show notification and open Exercises page
        self.notifier.notify('Time for a break', reason)
        # Switch to exercises page
        self.show_exercises()

    def _exercise_complete(self, exercise_name):
        # Called when an exercise finishes
        self.notifier.notify('Exercise complete', exercise_name)
        # update dashboard
        self.pages['dashboard'].refresh()


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
