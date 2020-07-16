import json
import functools
from typing import *

import requests

import citrine_client.errors as errors
import citrine_client.api.util as util
from citrine_client.server import SyncRequest, AsyncRequest, DaemonLink


__all__ = [
    'PackageClient',
    'CitrineClient',
]


class PackageClient(object):
    def __init__(self, host: str, port: int, autocancel: bool = True, async_: bool = False):
        self.server = DaemonLink(host=host, port=port)
        self.autocancel = autocancel
        self.async_ = async_
        if async_:
            self.Request = functools.partial(AsyncRequest, cancel=autocancel)
        else:
            self.Request = SyncRequest

    def install(
            self,
            name: Optional[str] = None,
            specfile: Optional[str] = None,
            localfile: Optional[str] = None,
            url: Optional[str] = None,
            package_hash: Optional[str] = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        request_data = util.package_install_params(name, specfile, localfile, url, package_hash)
        req = self.Request(
            server=self.server,
            endpoint='/package/install',
            **request_data,
        )
        if self.async_:
            return req.run(callback=progress_callback)  # daijoubu desu
        else:
            return req.run()

    def fetch(
            self,
            name: Optional[str] = None,
            specfile: Optional[str] = None,
            localfile: Optional[str] = None,
            url: Optional[str] = None,
            package_hash: Optional[str] = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        request_data = util.package_install_params(name, specfile, localfile, url, package_hash)
        req = self.Request(
            server=self.server,
            endpoint='/package/install',
            **request_data,
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def activate(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = self.Request(
            server=self.server,
            endpoint='/package/activate',
            jsn={'name': name, 'version': version},
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def deactivate(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = self.Request(
            server=self.server,
            endpoint='/package/deactivate',
            jsn={'name': name, 'version': version},
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def remove(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = self.Request(
            server=self.server,
            endpoint='/package/remove',
            jsn={'name': name, 'version': version},
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def list(
            self, 
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = self.Request(
            server=self.server,
            endpoint='/package/list',
            method='get',
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()
        
    def search(
            self,
            query: str,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = self.Request(
            server=self.server,
            endpoint='/package/search',
            jsn={'query': query},
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()


class CitrineClient(object):
    # Synchronous consumer of the asynchronous API
    def __init__(self, host: str, port: int, autocancel: bool = True, async_: bool = False):
        self.server = DaemonLink(host=host, port=port)
        self.package = PackageClient(host=host, port=port, autocancel=autocancel, async_=async_)
        self.autocancel = autocancel
        self.async_ = async_
        if async_:
            self.Request = functools.partial(AsyncRequest, cancel=autocancel)
        else:
            self.Request = SyncRequest

    def heartbeat(self) -> Dict:
        url = f'http://{self.server.host}:{self.server.port}/'
        resp = util.wrap_request(requests.get, url, timeout=10)
        try:
            return json.loads(resp.decode('utf-8'))
        except json.JSONDecodeError:
            raise errors.InvalidResponse('Server response was not JSON', data={'response': r.content.decode('utf-8')})

    def run(
            self,
            target: str,
            params: Dict = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        if not params:
            params = {}
        req = self.Request(
            server=self.server,
            endpoint=f'/run/{target}',
            jsn=params,
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def _run(
            self,
            target_package: str,
            target_model: str,
            params: Dict = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        # TODO: _run wants numpy arrays
        # Consider enforcing / coercing params to {str: np.ndarray}
        # Which might have implications for serialization (tensor protobuf?)
        if not params:
            params = {}
        req = self.Request(
            server=self.server,
            endpoint=f'/_run/{target_package}/{target_model}',
            jsn=params,
        )
        if self.async_:
            return req.run(callback=progress_callback)
        else:
            return req.run()

    def result(
            self,
            result_hash: str
    ) -> bytes:
        url = f'http://{self.server.host}:{self.server.port}/result/{result_hash}'
        resp = util.wrap_request(requests.get, url, timeout=10)
        return resp
