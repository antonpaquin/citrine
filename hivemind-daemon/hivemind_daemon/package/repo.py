import requests
from typing import *

from hivemind_daemon import errors, config

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


def index_lookup(name: str) -> Tuple[str, str]:
    global _package_index
    if _package_index is None:
        _package_index = {}
        _pull_index()
    if name not in _package_index:
        raise errors.PackageInstallError(f'Could not find package {name}')
    return _package_index[name]
