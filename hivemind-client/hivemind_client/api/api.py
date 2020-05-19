import json
from typing import *

import requests

import hivemind_client.errors as errors
import hivemind_client.api.util as util
from hivemind_client.server import AsyncRequest, DaemonLink


__all__ = [
    'PackageClient',
    'HivemindClient',
]


class PackageClient(object):
    def __init__(self, host: str, port: int):
        self.server = DaemonLink(host=host, port=port)
        
    def install(
            self,
            specfile: Optional[str] = None,
            localfile: Optional[str] = None,
            url: Optional[str] = None,
            package_hash: Optional[str] = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        request_data = util.package_install_params(specfile, localfile, url, package_hash)
        req = AsyncRequest(server=self.server, endpoint='/package/install', **request_data)
        return req.run(callback=progress_callback)
    
    def fetch(
            self,
            specfile: Optional[str] = None,
            localfile: Optional[str] = None,
            url: Optional[str] = None,
            package_hash: Optional[str] = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        request_data = util.package_install_params(specfile, localfile, url, package_hash)
        req = AsyncRequest(server=self.server, endpoint='/package/install', **request_data)
        return req.run(callback=progress_callback)
    
    def activate(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = AsyncRequest(server=self.server, endpoint='/package/activate', jsn={'name': name, 'version': version})
        return req.run(callback=progress_callback)
    
    def deactivate(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = AsyncRequest(server=self.server, endpoint='/package/deactivate', jsn={'name': name, 'version': version})
        return req.run(callback=progress_callback)
    
    def remove(
            self,
            name: str,
            version: Optional[str],
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = AsyncRequest(server=self.server, endpoint='/package/remove', jsn={'name': name, 'version': version})
        return req.run(callback=progress_callback)
    
    def list(
            self,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ):
        req = AsyncRequest(server=self.server, endpoint='/package/list', method='get')
        return req.run(callback=progress_callback)


class HivemindClient(object):
    # Async client
    def __init__(self, host: str, port: int):
        self.server = DaemonLink(host=host, port=port)
        self.package = PackageClient(host=host, port=port)

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
        req = AsyncRequest(server=self.server, endpoint=f'/run/{target}', jsn=params)
        return req.run(callback=progress_callback)

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
        req = AsyncRequest(server=self.server, endpoint=f'/_run/{target_package}/{target_model}', jsn=params)
        return req.run(callback=progress_callback)

    def result(
            self, 
            result_hash: str
    ) -> bytes:
        url = f'http://{self.server.host}:{self.server.port}/result/{result_hash}'
        resp = util.wrap_request(requests.get, url, timeout=10)
        return resp
