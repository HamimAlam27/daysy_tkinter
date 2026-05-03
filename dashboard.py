import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import json
import os
from datetime import datetime

# Matplotlib is optional; dashboard will still work without it.
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except Exception:
    HAS_MPL = False


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, data_path=None):
        super().__init__(parent, fg_color='transparent')
        self.data_path = data_path or os.path.join(os.path.expanduser('~'), '.microbreak_data.json')

        lbl = ctk.CTkLabel(self, text='Dashboard', font=('Segoe UI', 18, 'bold'))
        lbl.pack(pady=12, anchor='w', padx=12)

        self.summary = ctk.CTkLabel(self, text='No data yet', font=('Segoe UI', 11))
        self.summary.pack(pady=6, anchor='w', padx=12)

        # Chart area
        self.chart_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.chart_frame.pack(padx=12, pady=8, fill='both', expand=False)

        # Text fallback / details
        self.apps_box = tk.Text(self, height=10, width=60, bg='#0b0f14', fg='#d8e9df', bd=0)
        self.apps_box.pack(padx=12, pady=(4,12), fill='both', expand=True)

        self._chart_widget = None

    def refresh(self):
        today = datetime.now().strftime('%Y-%m-%d')
        if not os.path.exists(self.data_path):
            self.summary.configure(text='No data yet')
            self.apps_box.delete('1.0', 'end')
            self._clear_chart()
            return

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            self.summary.configure(text='Unable to read data')
            self._clear_chart()
            return

        day = data.get(today, {'apps': {}, 'exercises': [], 'ignored': 0})
        apps = day.get('apps', {})
        total = sum(apps.values())
        exercises = day.get('exercises', [])

        self.summary.configure(text=f"Today: {int(total)}s active · Exercises done: {len(exercises)} · Ignored: {day.get('ignored',0)}")

        # update text list
        self.apps_box.delete('1.0', 'end')
        if not apps:
            self.apps_box.insert('end', 'No app usage recorded for today')
        else:
            sorted_apps = sorted(apps.items(), key=lambda kv: -kv[1])
            for name, secs in sorted_apps[:50]:
                self.apps_box.insert('end', f"{name}: {int(secs)}s\n")

        # draw chart if matplotlib available
        if HAS_MPL:
            self._draw_bar_chart(apps)
        else:
            self._clear_chart()

    def _clear_chart(self):
        if self._chart_widget:
            try:
                self._chart_widget.get_tk_widget().destroy()
            except Exception:
                try:
                    self._chart_widget.destroy()
                except Exception:
                    pass
        self._chart_widget = None

    def _draw_bar_chart(self, apps):
        # remove previous
        self._clear_chart()

        fig = Figure(figsize=(6, 2.6), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0b0f14')
        fig.patch.set_facecolor('#0b0f14')

        if not apps:
            ax.text(0.5, 0.5, 'No data', horizontalalignment='center', verticalalignment='center', color='white', fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            sorted_apps = sorted(apps.items(), key=lambda kv: kv[1])
            names = [n for n, s in sorted_apps]
            secs = [s for n, s in sorted_apps]
            ax.barh(names, secs, color='#58d19e')
            ax.set_xlabel('Seconds', color='white')
            ax.tick_params(colors='white')

        fig.tight_layout()

        try:
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(fill='both', expand=True)
            self._chart_widget = canvas
        except Exception:
            # fail silently and leave text list
            self._chart_widget = None
