import requests
from typing import *

from citrine_daemon import errors, config

_package_index: Dict[str, Tuple[str, str]] = None


def _pull_index():
    url = config.get_config('repository_url')
    try:
        r = requests.get(url, timeout=10)
        data = r.text.strip().split('\n')
    except requests.exceptions.RequestException:
        raise errors.RepositoryError(f'Could not sync repository from {url}')
    for row in data:
        name, pkg_url, pkg_hash = row.split('|')
        _package_index[name] = (pkg_url, pkg_hash)
        
        
def _get_index():
    global _package_index
    if _package_index is None:
        _package_index = {}
        _pull_index()
    return _package_index

        
def search_package(query: str):
    package_index = _get_index()
    return {
        'packages': [name for name in package_index.keys() if query.lower() in name.lower()]
    }


def index_lookup(name: str) -> Tuple[str, str]:
    package_index = _get_index()
    if name not in package_index:
        raise errors.PackageInstallError(f'Could not find package {name}')
    return package_index[name]
