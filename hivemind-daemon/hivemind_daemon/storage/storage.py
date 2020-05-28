import logging
import os

import hivemind_daemon.package.db as db
from hivemind_daemon.config import get_config

__all__ = [
    'root_path',
    'results_rel',
    'results_path',
    'package_rel',
    'package_path',
    'download_rel',
    'download_path',
    'get_package_module',
    'get_package_json',
    'get_model_file',
    'init_storage',
]


logger = logging.getLogger(__name__)


# TODO windows support for storage
# I think windows wants appdata something or other?
def root_path():
    return get_config('storage_path')


results_rel = 'results'
def results_path():
    return os.path.join(root_path(), results_rel)


package_rel = 'package'
def package_path():
    return os.path.join(root_path(), package_rel)


download_rel = 'downloads'
def download_path():
    return os.path.join(root_path(), download_rel)


def get_package_module(package: db.DBPackage) -> str:
    return os.path.join(package_path(), package.install_path, 'module.py')


def get_package_json(package: db.DBPackage) -> str:
    return os.path.join(package_path(), package.install_path, 'package.json')


def get_model_file(model: db.DBModel) -> str:
    return os.path.join(package_path(), model.install_path)


def init_storage():
    logger.info(f'Initializing hivemind storage at {root_path()}', {'root_path': root_path()})
    for path in [
        root_path(),
        results_path(),
        package_path(),
        download_path(),
    ]:
        os.makedirs(path, exist_ok=True)
