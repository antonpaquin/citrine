import asyncio
import queue
import threading
from typing import *

import websockets

from hivemind_ui.js_bridge.util import AsyncTunnel
from hivemind_ui.config import get_config


__all__ = [
    'init_server',
    'claim_connection',
]

server_event_loop = asyncio.new_event_loop()
claims = AsyncTunnel(server_event_loop)


# wtf


def init_server():
    def server_thread():
        start_server = websockets.serve(
            ws_handler=serve, 
            host="localhost", 
            port=get_config('js_bridge.socket.port'), 
            loop=server_event_loop,
            max_size=2**30,
        )
        server_event_loop.run_until_complete(start_server)
        server_event_loop.run_forever()
        
    t = threading.Thread(target=server_thread, daemon=True)
    t.start()


def claim_connection(name: str, recv_fn: Callable[[str], Any]) -> Callable[[str], Any]:
    send_fn = claims.send(name, recv_fn)
    return send_fn


async def get_claimant(claimant: str, send_fn: Callable[[str], Any]) -> Callable[[str], Any]:
    recv_fn = await claims.send_async(claimant, send_fn)
    return recv_fn


async def serve(websocket: websockets.WebSocketServerProtocol, path: str):
    connection_closed = None

    claimant = path[1:]

    # Having performance issues with the default AIO queue
    # So, just manually implement a replacement
    msg_queue = queue.Queue()
    queue_wake = asyncio.Event()

    def send_fn(msg: str) -> None:
        if connection_closed is not None:
            raise connection_closed
        msg_queue.put(msg)
        server_event_loop.call_soon_threadsafe(queue_wake.set)

    on_recv = await get_claimant(claimant, send_fn)

    async def serve_send():
        try:
            while True:
                await queue_wake.wait()
                while not msg_queue.empty():
                    msg = msg_queue.get()
                    await websocket.send(msg)
                queue_wake.clear()
        except websockets.ConnectionClosed:
            pass
        
    async def serve_recv():
        nonlocal connection_closed
        try:
            while True:
                msg = await websocket.recv()
                on_recv(msg)
        except websockets.ConnectionClosed as e:
            connection_closed = e

    await asyncio.gather(serve_send(), serve_recv())
