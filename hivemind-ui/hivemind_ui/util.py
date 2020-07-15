import os
import queue
import threading
import traceback

threadpool = []
work_queue = queue.Queue()


def init_threadpool():
    global threadpool
    threadpool = [threading.Thread(target=worker_thread, daemon=True, name=f'Worker-{idx}') for idx in range(16)]
    [t.start() for t in threadpool]


def worker_thread():
    while True:
        try:
            fn, args = work_queue.get()
            fn(*args)
        except Exception as e:
            print(f'Error in thread: {e}')
            traceback.print_exc()


def threaded(f):
    def wrapped(*args):
        work_queue.put((f, args))
    return wrapped


def get_root_path():
    fpath = os.path.abspath(__file__)
    for _ in range(1):
        fpath = os.path.dirname(fpath)
    return fpath


def get_resource(path: str) -> str:
    return os.path.join(get_root_path(), 'res', path)