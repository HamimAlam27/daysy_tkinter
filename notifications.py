try:
    from win10toast import ToastNotifier
except Exception:
    ToastNotifier = None

class Notifier:
    def __init__(self):
        self._impl = None
        if ToastNotifier:
            try:
                self._impl = ToastNotifier()
            except Exception:
                self._impl = None

    def notify(self, title, msg):
        if self._impl:
            try:
                self._impl.show_toast(title, msg, duration=6, threaded=True)
                return
            except Exception:
                pass
        # fallback
        print(f"NOTIFICATION: {title} - {msg}")
