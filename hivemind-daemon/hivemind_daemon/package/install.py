import os
import shutil
import tempfile
import typing
import uuid
import zipfile

from hivemind_daemon import errors, storage
import hivemind_daemon.package.db as db
from hivemind_daemon.package.load import load_package_json, _activate_package


def install_package_file(localfile: str, activate: bool):
    if not os.path.exists(localfile):
        raise errors.PackageInstallError(f'Could not find local package {localfile}', 400)
    with tempfile.TemporaryDirectory() as tmpdir:
        if os.path.isdir(localfile):
            os.rmdir(tmpdir)  # easier this way, and I think tempfile isn't messing with inodes
            shutil.copytree(localfile, tmpdir)
        elif os.path.isfile(localfile):
            try:
                with zipfile.ZipFile(localfile) as zip_f:
                    for fname in zip_f.filelist:
                        zip_f.extract(fname, tmpdir)
            except zipfile.BadZipFile:
                raise errors.PackageInstallError(f'Package at {localfile} was not a valid zip archive')
        db_package = install_from_temp(tmpdir)
    if activate:
        _activate_package(db_package)
    return {'status': 'OK'}


def install_package_url(url: str, package_hash: str, activate: bool):
    dl_file = storage.download.get_file(url, package_hash)
    return install_package_file(dl_file, activate)

        
def prep_copy(unpack_dir: str, install_dir: str, package_meta: typing.Dict) -> typing.List[typing.Tuple[str, str]]:
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


def check_paths(install_paths: typing.List[typing.Tuple[str, str]]):
    for from_path, _ in install_paths:
        if not os.path.isfile(from_path):
            raise errors.PackageInstallError(f'Package is missing file {from_path}', 400)


def install_from_temp(unpack_dir: str) -> db.DBPackage:
    if not os.path.isfile(os.path.join(unpack_dir, 'package.json')):
        raise errors.PackageInstallError(f'No package.json at {unpack_dir}', 400)

    package_meta = load_package_json(os.path.join(unpack_dir, 'package.json'))
    
    install_id = str(uuid.uuid4())
    install_dir = os.path.join(storage.package_path, str(uuid.uuid4()))
    install_paths = prep_copy(unpack_dir, install_dir, package_meta)
    
    check_paths(install_paths)

    os.makedirs(install_dir)
    for from_path, to_path in install_paths:
        shutil.copy(from_path, to_path)
        
    return db.install_package(package_meta, install_id)


def list_packages():
    return os.listdir(storage.package_path)
