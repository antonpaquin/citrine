import json
import time
from typing import Dict, Optional

import requests

import citrine_client.errors as errors


class DaemonLink(object):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port


class CitrineRequest(object):
    default_timeout = 10

    def __init__(
            self,
            server: DaemonLink,
            endpoint: str,
            params: Optional[Dict] = None,
            files: Optional[Dict[str, bytes]] = None,
            jsn: Optional[Dict] = None,
            method: str = 'post',
            timeout: float = None,
    ):
        """
        :param server:
        :param endpoint:
        :param params: Passed to requests 'params'
        :param files: Passed to requests 'files'
        :param jsn: Passed to requests 'json'
        :param method: Which HTTP method to use
        """
        self.server = server
        self.method = method
        if timeout is None:
            self.timeout = self.default_timeout
        else:
            self.timeout = timeout

        self.url = f'http://{server.host}:{server.port}{endpoint}'
        self.request_args = {}
        if params is not None:
            self.request_args['params'] = params
        if files is not None:
            self.request_args['files'] = files
        if json is not None:
            self.request_args['json'] = jsn

    def send(self):
        try:
            if self.method == 'post':
                r = requests.post(self.url, **self.request_args, timeout=self.timeout)
            elif self.method == 'get':
                r = requests.get(self.url, **self.request_args, timeout=self.timeout)
            else:
                r = requests.request(self.method, self.url, **self.request_args, timeout=self.timeout)
        except requests.exceptions.ConnectTimeout:
            raise errors.ConnectionError('Connection timed out')
        except requests.exceptions.ConnectionError:
            raise errors.ConnectionRefused('Cannot connect to server')

        resp = self._parse_response(r)
        return resp
    
    def run(self):
        raise NotImplementedError('Stub!')

    @staticmethod
    def _parse_response(response):
        try:
            resp = json.loads(response.content)
        except json.JSONDecodeError:
            raise errors.ServerError('Malformed server response', data={'response': response.content.decode('utf-8')})
        if response.status_code != 200:
            raise errors.ServerError('Server rejected request', data=resp)
        return resp
    
               cancel: bool = True

class SyncRequest(CitrineRequest):
    default_timeout = 60
    def run(self):
        return self.send()


class AsyncRequest(CitrineRequest):
    def __init__(
            self,
            server: DaemonLink,
            endpoint: str,
            params: Optional[Dict] = None,
            files: Optional[Dict[str, bytes]] = None,
            jsn: Optional[Dict] = None,
            method: str = 'post',
            cancel: bool = True,
            timeout: float = None,
    ):
        """
        :param cancel:
            If the request fails or is interrupted before it completes, should we send a cancellation request?
        """
        super().__init__(
            server=server,
            endpoint=endpoint,
            params=params,
            files=files,
            jsn=jsn,
            method=method,
            timeout=timeout,
        )
        self.url = f'http://{server.host}:{server.port}/async{endpoint}'
        self.cancel = cancel
        
        self.uid = None  # type: Optional[str]
        self.status = None  # type: Optional[str]
        self.data = None  # type: Optional[Dict]
        self.result = None  # type: Optional[Dict]
        self.error = None  # type: Optional[Dict]

    def refresh(self):
        url_update = f'http://{self.server.host}:{self.server.port}/async/get/{self.uid}'
        try:
            r = requests.get(url_update, timeout=10)
        except requests.exceptions.ConnectTimeout:
            raise errors.ConnectionError('Connection timed out')
        except requests.exceptions.ConnectionError:
            raise errors.ConnectionRefused('Cannot connect to server')
        resp = self._parse_response(r)
        self._update(resp)

    def _update(self, response):
        self.uid = response['uid']
        self.status = response['status']
        self.data = response['data']
        if 'result' in response:
            self.result = response['result']
        if 'error' in response:
            self.error = response['error']

    def run(self, callback=None):
        with self:
            while not self.done:
                time.sleep(0.1)
                self.refresh()
                if callback and self.data:
                    callback(self.data)
        if self.status == 'Error':
            raise errors.ServerError('Request failed', data=self.error)
        return self.result

    def send(self):
        resp = super().send()
        self._update(resp)
        return resp

    def __enter__(self):
        self.send()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.done:
            return
        if not self.cancel:
            return
        url_cancel = f'http://{self.server.host}:{self.server.port}/async/cancel/{self.uid}'
        try:
            requests.get(url_cancel, timeout=1)
        except Exception:
            pass

    @property
    def done(self):
        return self.status in {'Error', 'Done'}
