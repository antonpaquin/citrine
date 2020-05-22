import threading


def threaded(f):
    def wrapped(self, *args):
        t = threading.Thread(target=f, daemon=True, args=(self, *args))
        t.start()
    return wrapped
