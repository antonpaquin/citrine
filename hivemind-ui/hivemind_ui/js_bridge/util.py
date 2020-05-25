import asyncio
import queue
import threading
from typing import *


class AsyncTunnel:
    # We need to cross thread _and_ asyncio boundaries
    # It's quite tedious

    # A sends to B and blocks until B has sent to A
    # B sends to A and awaits until A has sent to B

    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        self.event_loop = event_loop
        self._lock = threading.Lock()
        self.a_to_b = {}  # type: Dict[str, Any]
        self.b_to_a = {}  # type: Dict[str, queue.Queue]
        self.notify = {}  # type: Dict[str, Callable]  # the "set" function for AIO events that B is waiting on

    def send(self, key, value, timeout=1000):
        if key in self.a_to_b:
            raise KeyError("Key already in use")
        with self._lock:
            self.a_to_b[key] = value
            if key in self.notify:
                self.event_loop.call_soon_threadsafe(self.notify[key])
            if key not in self.b_to_a:
                self.b_to_a[key] = queue.Queue()
        res = self.b_to_a[key].get(timeout=timeout)
        self.b_to_a.pop(key, None)
        self.notify.pop(key, None)
        return res

    async def send_async(self, key, value):
        if key in self.b_to_a:
            raise KeyError("Key already in use")
        with self._lock:  # yes, locking the event loop. I promise it won't be for long.
            if key not in self.b_to_a:
                self.b_to_a[key] = queue.Queue()
            # In practice, 'block=False' shouldn't matter. However, better to be explicit.
            self.b_to_a[key].put(value, block=False)
            if key in self.a_to_b:
                return self.a_to_b[key]
            waiter = asyncio.Event()
            self.notify[key] = waiter.set
        await waiter.wait()
        return self.a_to_b.pop(key)
