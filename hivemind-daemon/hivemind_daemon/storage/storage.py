import os

import hivemind_daemon.package.db as db

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


# TODO windows support for storage
# I think windows wants appdata something or other?
root_path = os.path.join(os.getenv('HOME'), '.cache', 'hivemind')

results_rel = 'results'
results_path = os.path.join(root_path, results_rel)

package_rel = 'package'
package_path = os.path.join(root_path, package_rel)

download_rel = 'downloads'
download_path = os.path.join(root_path, download_rel)


def get_package_module(package: db.DBPackage) -> str:
    return os.path.join(package_path, package.install_path, 'module.py')


def get_package_json(package: db.DBPackage) -> str:
    return os.path.join(package_path, package.install_path, 'package.json')


def get_model_file(model: db.DBModel) -> str:
    return os.path.join(package_path, model.install_path)


def init_storage():
    for path in [
        root_path,
        results_path,
        package_path,
        download_path,
    ]:
        os.makedirs(path, exist_ok=True)
