import os
import json
import queue
import threading
from typing import *
import uuid

from PySide2.QtWebEngineWidgets import QWebEngineScript
import citrine_client

from citrine_ui.config import get_config


cached_js = None


class CitrineJSClient(QWebEngineScript):
    def __init__(self):
        super().__init__()

        self.setWorldId(QWebEngineScript.MainWorld)
        self.setInjectionPoint(QWebEngineScript.DocumentCreation)
        
        self.key = str(uuid.uuid4())
        socket_port = get_config('js_bridge.socket.port')
        daemon_server = get_config('daemon.server')
        daemon_port = get_config('daemon.port')
        prepend_src = (
            f'var _citrine_port = "{socket_port}";\n'
            f'var _citrine_key = "{self.key}";\n'
            f'var _citrine_daemon_server = "{daemon_server}";\n'
            f'var _citrine_daemon_port = {daemon_port};\n'
        )
        self.setSourceCode(prepend_src + get_js_client())


class CitrineBridgeClient:
    def __init__(self):
        self.client = citrine_client.CitrineClient(get_config('daemon.server'), get_config('daemon.port'))
        self.client.heartbeat()
        self.send = None
        # Set up a queue to hold any messages sent in the interval between when on_recv is received by the async server
        # and the resulting "send" is bound here
        # This is happens in
        #   bridge_client.bind_send(js_bridge.claim_connection(key, bridge_client.on_recv))
        # So it's a small but nonzero interval (after claim_connection starts, before bind_send returns)
        self.prebind_send_queue = queue.Queue()
        
    def bind_send(self, send_fn: Callable[[str], Any]):
        self.send = send_fn
        while not self.prebind_send_queue.empty():
            self.send(self.prebind_send_queue.get())
        self.prebind_send_queue = None

    def on_recv(self, msg: str):
        jsn = json.loads(msg)
        cmd = {
            'heartbeat': self.client.heartbeat,
            'run': self.client.run,
            '_run': self.client._run,
            'result': self.client.result,
            'package.install': self.client.package.install,
            'package.fetch': self.client.package.fetch,
            'package.activate': self.client.package.activate,
            'package.deactivate': self.client.package.deactivate,
            'package.remove': self.client.package.remove,
            'package.list': self.client.package.list,
            'bridge.get_daemon': self.get_daemon,
        }.get(jsn['cmd'])
        
        def cmd_thread():
            try:
                results = cmd(**jsn['params'])
                reply = json.dumps({
                    'id': jsn['id'],
                    'results': results,
                    'success': True,
                })
            except citrine_client.errors.CitrineClientError as e:
                reply = json.dumps({
                    'id': jsn['id'],
                    'error': e.to_dict(),
                    'success': False,
                })

            if self.send is None:
                self.prebind_send_queue.put(reply)
            else:
                self.send(reply)

        t = threading.Thread(target=cmd_thread, daemon=True)
        t.start()

    def get_daemon(self):
        return {'server': get_config('daemon.server'), 'port': get_config('daemon.port')}


def get_js_client():
    global cached_js
    if cached_js is None:
        fpath = os.path.join(os.path.dirname(__file__), 'client.js')
        with open(fpath) as in_f:
            cached_js = in_f.read()
    return cached_js
