import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, data_path=None):
        super().__init__(parent)
        self.data_path = data_path or os.path.join(os.path.expanduser('~'), '.microbreak_data.json')

        lbl = ttk.Label(self, text='Dashboard', font=('Segoe UI', 16))
        lbl.pack(pady=12)

        self.summary = ttk.Label(self, text='No data yet')
        self.summary.pack(pady=6)

        self.apps_box = tk.Text(self, height=15, width=60, bg='#0f1113', fg='white')
        self.apps_box.pack(padx=12, pady=8)

    def refresh(self):
        today = datetime.now().strftime('%Y-%m-%d')
        if not os.path.exists(self.data_path):
            self.summary.config(text='No data yet')
            self.apps_box.delete('1.0', 'end')
            return

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            self.summary.config(text='Unable to read data')
            return

        day = data.get(today, {'apps': {}, 'exercises': []})
        total = sum(day.get('apps', {}).values())
        exercises = day.get('exercises', [])

        self.summary.config(text=f"Today: {int(total)}s active · Exercises done: {len(exercises)}")

        self.apps_box.delete('1.0', 'end')
        apps = day.get('apps', {})
        if not apps:
            self.apps_box.insert('end', 'No app usage recorded for today')
            return

        sorted_apps = sorted(apps.items(), key=lambda kv: -kv[1])
        for name, secs in sorted_apps[:50]:
            self.apps_box.insert('end', f"{name}: {int(secs)}s\n")
