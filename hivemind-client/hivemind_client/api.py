import json
import os
import time
from typing import Optional, Callable, Dict

import requests

import hivemind_client.errors as errors
from hivemind_client.server import get_server, AsyncRequest, DaemonLink


__all__ = [
    'PackageClient',
    'HivemindClient',
    'install',
    'daemon_install',
    'heartbeat',
    'run',
    '_run',
    'result',
]


def install(
        fname: str,
        progress_callback: Optional[Callable[[Dict], None]] = None,
) -> Dict:
    server = get_server()
    return PackageClient(server.host, server.port).install(fname, progress_callback)


def daemon_install(
        package_type: str,
        link: str,
        package_hash: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict], None]] = None,
) -> Dict:
    server = get_server()
    return PackageClient(server.host, server.port).daemon_install(package_type, link, package_hash, progress_callback)


def heartbeat() -> Dict:
    server = get_server()
    return HivemindClient(server.host, server.port).heartbeat()


def run(
        target: str,
        params: Dict = None,
        progress_callback: Optional[Callable[[Dict], None]] = None,
) -> Dict:
    server = get_server()
    return HivemindClient(server.host, server.port).run(target, params, progress_callback)


def _run(
        target_package: str,
        target_model: str,
        params: Dict = None,
        progress_callback: Optional[Callable[[Dict], None]] = None,
) -> Dict:
    server = get_server()
    return HivemindClient(server.host, server.port)._run(target_package, target_model, params, progress_callback)


def result(result_hash: str) -> bytes:
    server = get_server()
    return HivemindClient(server.host, server.port).result(result_hash)


class PackageClient(object):
    def __init__(self, host: str, port: int):
        self.server = DaemonLink(host=host, port=port)
    
    def install(
            self,
            fname: str,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        if not os.path.isfile(fname):
            raise errors.FileNotFound(f'Could not find file {fname}')
        with open(fname, 'rb') as in_f:
            filedata = in_f.read()

        req = AsyncRequest(server=self.server, endpoint='/package/install', files={'hivespec': filedata})
        with req:
            while not req.done:
                time.sleep(0.1)
                req.refresh()
                if progress_callback and req.data:
                    progress_callback(req.data)

        if req.status == 'Error':
            raise errors.ServerError('Request failed', data=req.error)

        return req.result

    def daemon_install(
            self,
            package_type: str,
            link: str,
            package_hash: Optional[str] = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        if package_type == 'url':
            if package_hash is None:
                raise errors.InvalidOptions('Package type "url" requires hash')
            params = {'type': package_type, 'link': link, 'hash': package_hash}
        elif package_type == 'file':
            if package_hash is not None:
                raise errors.InvalidOptions('Package type "file" does not check hash')
            params = {'type': package_type, 'link': link}
        else:
            raise errors.InvalidOptions('Invalid package type')

        req = AsyncRequest(server=self.server, endpoint='/package/daemon_install', jsn=params)
        with req:
            while not req.done:
                time.sleep(0.1)
                req.refresh()
                if progress_callback and req.data:
                    progress_callback(req.data)

        if req.status == 'Error':
            raise errors.ServerError('Request failed', data=req.error)

        return req.result


class HivemindClient(object):
    def __init__(self, host: str, port: int):
        self.server = DaemonLink(host=host, port=port)
        self.package = PackageClient(host=host, port=port)

    def heartbeat(self) -> Dict:
        url = f'http://{self.server.host}:{self.server.port}/'
        r = None
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            raise errors.ServerError('Connection timed out', data={'host': self.server.host, 'port': self.server.port})
        except requests.exceptions.HTTPError:
            raise errors.ServerError('Request failed', data={'response': r.content.decode('utf-8')})
        except requests.exceptions.ConnectionError:
            raise errors.ConnectionRefused('Failed to connect to server')
        try:
            return json.loads(r.content.decode('utf-8'))
        except json.JSONDecodeError:
            raise errors.InvalidResponse('Server response was not JSON', data={'response': r.content.decode('utf-8')})

    def run(
            self,
            target: str, 
            params: Dict = None,
            progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        server = get_server()

        if not params:
            params = {}

        req = AsyncRequest(server=server, endpoint=f'/run/{target}', jsn=params)
        with req:
            while not req.done:
                time.sleep(0.1)
                req.refresh()
                if progress_callback and req.data:
                    progress_callback(req.data)

        if req.status == 'Error':
            raise errors.ServerError('Request failed', data=req.error)

        return req.result

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
        with req:
            while not req.done:
                time.sleep(0.1)
                req.refresh()
                if progress_callback and req.data:
                    progress_callback(req.data)

        if req.status == 'Error':
            raise errors.ServerError('Request failed', data=req.error)

        return req.result

    def result(
            self, 
            result_hash: str
    ) -> bytes:
        server = get_server()
        url = f'http://{server.host}:{server.port}/result/{result_hash}'
        r = requests.get(url)
        if r.status_code != 200:
            raise errors.ServerError('Request failed', data={'response': r.content.decode('utf-8')})
        return r.content
