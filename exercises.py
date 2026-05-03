import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import math

class TimerCanvas(tk.Canvas):
    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self.size = size
        self.arc = None
        self.text = None

    def draw(self, fraction, text):
        self.delete('all')
        cx = cy = self.size / 2
        r = self.size * 0.42
        start = -90
        extent = fraction * 360
        # background circle (subtle)
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline='#21313a', width=14)
        # progress arc with gradient-like single color
        self.create_arc(cx - r, cy - r, cx + r, cy + r, start=start, extent=extent, style='arc', outline='#58d19e', width=14)
        # center text
        self.create_text(cx, cy, text=text, fill='#e6f7ef', font=('Segoe UI', 16, 'bold'))


class ExercisesFrame(ctk.CTkFrame):
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.on_complete = on_complete

        self.exercises = [
            ('Box Breathing', 60),
            ('Little Stretch', 45),
            ('Drink Water', 30),
            ('Little Walk', 300)
        ]

        left = ctk.CTkFrame(self, width=220, fg_color='transparent')
        left.pack(side='left', fill='y', padx=20, pady=20)

        lbl = ctk.CTkLabel(left, text='Exercises', font=('Segoe UI', 16, 'bold'))
        lbl.pack(pady=6)

        for name, sec in self.exercises:
            btn = ctk.CTkButton(left, text=f"{name} — {sec}s", command=lambda n=name, s=sec: self.start_exercise(n, s))
            btn.pack(fill='x', pady=6)

        self.right = ctk.CTkFrame(self, fg_color='transparent')
        self.right.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        self.canvas = TimerCanvas(self.right, size=260, bg='#0b0f14')
        self.canvas.pack(pady=30)

        self.current = None
        self._running = False
    def start_exercise(self, name, seconds):
        self.current = {'name': name, 'total': seconds, 'left': seconds}
        if not self._running:
            self._running = True
            self._tick()

    def _tick(self):
        if not self.current:
            self.canvas.draw(0, '')
            self._running = False
            return

        left = self.current['left']
        total = self.current['total']
        fraction = (total - left) / total if total else 0
        self.canvas.draw(fraction, f"{left}s")

        if left <= 0:
            name = self.current['name']
            self.current = None
            self._running = False
            if self.on_complete:
                self.on_complete(name)
            return

        self.current['left'] -= 1
        self.after(1000, self._tick)
