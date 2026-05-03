import threading
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import os
import json
from datetime import datetime

from monitor import ActivityMonitor
from exercises import ExercisesFrame
from dashboard import DashboardFrame
from notifications import Notifier

APP_DATA = os.path.join(os.path.expanduser('~'), '.microbreak_data.json')

class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('dark-blue')

        super().__init__()
        self.title('MicroBreak — Intelligent Breaks')
        self.geometry('900x600')

        self.notifier = Notifier(self)

        # appearance tweaks
        self._create_layout()

        # session_limit_seconds set to 10s for testing break suggestion
        self.monitor = ActivityMonitor(on_break_suggested=self._on_break_suggested,
                                       stats_path=APP_DATA,
                                       session_limit_seconds=10)
        self.monitor_thread = None

    def _create_layout(self):
        container = ctk.CTkFrame(self, corner_radius=0)
        container.pack(fill='both', expand=True)

        sidebar = ctk.CTkFrame(container, width=220, corner_radius=0)
        sidebar.pack(side='left', fill='y')

        self.main = ctk.CTkFrame(container, corner_radius=0)
        self.main.pack(side='right', fill='both', expand=True)

        # Header inside main for a modern app feel
        header = ctk.CTkFrame(self.main, height=64, corner_radius=0)
        header.pack(side='top', fill='x')
        title = ctk.CTkLabel(header, text='MicroBreak', font=('Segoe UI', 20, 'bold'))
        title.pack(side='left', padx=16, pady=12)
        subtitle = ctk.CTkLabel(header, text='Smart micro-breaks', font=('Segoe UI', 12))
        subtitle.pack(side='left', padx=8, pady=16)

        # Sidebar buttons
        # Sidebar with simple icons using CTkButtons
        def _mk_btn(text, cmd):
            def _wrapped():
                try:
                    cmd()
                except Exception as e:
                    print(f'Button callback error for {text}:', e)
            btn = ctk.CTkButton(sidebar, text=text, fg_color='transparent', command=_wrapped)
            btn.pack(fill='x', padx=12, pady=10)
            return btn

        btn_home = _mk_btn('🏠  Home', self.show_home)
        btn_dash = _mk_btn('📊  Dashboard', self.show_dashboard)
        btn_ex = _mk_btn('🏃  Exercises', self.show_exercises)
        btn_quit = _mk_btn('⏻  Quit', self.destroy)

        # Pages
        self.pages = {}
        self.pages['home'] = self._build_home(self.main)
        self.pages['dashboard'] = DashboardFrame(self.main, data_path=APP_DATA)
        self.pages['exercises'] = ExercisesFrame(self.main, on_complete=self._exercise_complete)

        self.show_home()

    def _build_home(self, parent):
        f = ctk.CTkFrame(parent, corner_radius=8)

        # Card for home content
        card = ctk.CTkFrame(f, corner_radius=8, fg_color='#0f1418')
        card.pack(padx=20, pady=24, fill='x')

        lbl = ctk.CTkLabel(card, text='Welcome to MicroBreak', font=('Segoe UI', 20, 'bold'))
        lbl.pack(anchor='w', pady=(6,0), padx=8)

        self.status_var = tk.StringVar(value='Monitor stopped')
        status = ctk.CTkLabel(card, textvariable=self.status_var, text_color='#9aa6b2', font=('Segoe UI', 11))
        status.pack(anchor='w', pady=(6,0), padx=8)

        btn_row = ctk.CTkFrame(card, fg_color='transparent')
        btn_row.pack(anchor='w', pady=12, padx=8)

        def _start_wrapped():
            try:
                self.toggle_monitor()
            except Exception as e:
                print('Start button error:', e)

        self.start_btn = ctk.CTkButton(btn_row, text='Start Monitor', fg_color='#3fb57e', command=_start_wrapped)
        self.start_btn.pack(side='left')

        self.elapsed_var = tk.StringVar(value='Elapsed: 0s')
        elapsed_lbl = ctk.CTkLabel(btn_row, textvariable=self.elapsed_var, text_color='#9aa6b2', font=('Segoe UI', 11))
        elapsed_lbl.pack(side='left', padx=14)

        # Ignored breaks counter
        self.ignored_var = tk.IntVar(value=0)
        self._ignored_label_var = tk.StringVar(value=f'Ignored breaks: {self.ignored_var.get()}')
        ignored_lbl = ctk.CTkLabel(card, textvariable=self._ignored_label_var, text_color='#9aa6b2', font=('Segoe UI', 11))
        ignored_lbl.pack(anchor='w', pady=(6,0), padx=8)

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
            self.start_btn.configure(text='Start Monitor')
            self.status_var.set('Monitor stopped')
            self._start_time = None
        else:
            self.monitor.start()
            self.start_btn.configure(text='Stop Monitor')
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
