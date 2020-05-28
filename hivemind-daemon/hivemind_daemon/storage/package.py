import logging
import os
import shutil
from typing import Dict, Tuple, List

from hivemind_daemon import errors, package
from hivemind_daemon.storage.storage import package_path


logger = logging.getLogger(__name__)


def prep_copy(unpack_dir: str, install_dir: str, package_meta: Dict) -> List[Tuple[str, str]]:
    res = []
    package_from = os.path.join(unpack_dir, 'package.json')
    package_to = os.path.join(install_dir, 'package.json')
    res.append((package_from, package_to))

    module_from = os.path.join(unpack_dir, package_meta['module'])
    module_to = os.path.join(install_dir, 'module.py')
    res.append((module_from, module_to))

    for model_name, model_spec in package_meta['model'].items():
        model_from = os.path.join(unpack_dir, model_spec['file'])
        model_to = os.path.join(install_dir, f'{model_name}.{model_spec["type"]}')
        res.append((model_from, model_to))

    return res


def check_paths(install_paths: List[Tuple[str, str]]):
    for from_path, _ in install_paths:
        if not os.path.isfile(from_path):
            raise errors.PackageInstallError(f'Package is missing file {from_path}', 400)


def install_from_temp(unpack_dir: str, install_id: str, package_meta: Dict):
    if not os.path.isfile(os.path.join(unpack_dir, 'package.json')):
        raise errors.PackageInstallError(f'No package.json at {unpack_dir}', 400)

    install_dir = os.path.join(package_path(), install_id)
    install_paths = prep_copy(unpack_dir, install_dir, package_meta)

    check_paths(install_paths)

    logger.info(f'Installing package files to hivemind cache {install_dir}', {'install_dir': install_dir})
    os.makedirs(install_dir)
    for from_path, to_path in install_paths:
        shutil.copy(from_path, to_path)


def remove(install_id: str):
    install_path = os.path.join(package_path(), install_id)
    
    if not os.path.isdir(install_path):
        logger.warning('Will remove a package, but package files do not exist. This is probably okay.')
        # raise errors.PackageStorageError(f'Package at {install_path} was missing')
        # Remove something that doesn't exist? This is probably OK
        # Likely means that the package was removed some other way and the user just wants to purge it from the DB
        # Maybe log a warning once I've got that
        return

    logger.info(f'Removing files at {install_path}', {'install_path': install_path})
    shutil.rmtree(install_path)
