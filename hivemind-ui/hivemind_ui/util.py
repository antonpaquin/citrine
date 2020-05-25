import os
import threading


def threaded(f):
    def wrapped(*args):
        t = threading.Thread(target=f, daemon=True, args=args)
        t.start()
    return wrapped


def get_root_path():
    fpath = os.path.abspath(__file__)
    for _ in range(1):
        fpath = os.path.dirname(fpath)
    return fpath


def get_resource(path: str) -> str:
    return os.path.join(get_root_path(), 'res', path)