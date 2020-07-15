import logging
import os
import shutil
import tempfile
from typing import Optional, Dict
import uuid
import zipfile

from hivemind_daemon import errors, storage, core, package
from hivemind_daemon.package import repo


logger = logging.getLogger(__name__)


def install_package_file(localfile: str, activate: bool, exist_ok: bool = None) -> Dict:
    # The cross-package complexity of this is a little annoying
    # Take advantage of opportunities to simplify
    logger.info(f'Installing new package from file {localfile}', {'localfile': localfile})

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
        logger.debug(f'Package unpacked to {tmpdir}', {'tmpdir': tmpdir})

        package_meta = package.load.load_package_meta(os.path.join(tmpdir, 'meta.json'))
        install_id = str(uuid.uuid4())
        if exist_ok:
            try:
                db_package = package.db.install_package(package_meta, install_id)
            except errors.PackageAlreadyExists:
                return {'status': 'OK', 'note': 'Package Already Installed'}
        else:
            db_package = package.db.install_package(package_meta, install_id)

        storage.package.install_from_temp(tmpdir, install_id, package_meta)

    if activate:
        package.load.set_package_active(db_package, True)

    return {'status': 'OK'}


def install_package_url(url: str, package_hash: str, activate: bool, exist_ok: bool = None) -> Dict:
    dl_file = storage.download.get_file(url, package_hash)
    return install_package_file(dl_file, activate, exist_ok=exist_ok)


def install_package_name(name: str, activate: bool, exist_ok: bool = None) -> Dict:
    pkg_url, pkg_hash = repo.index_lookup(name)
    return install_package_url(pkg_url, pkg_hash, activate, exist_ok=exist_ok)


def remove_package(name: str, version: Optional[str]):
    from hivemind_daemon.package import DBPackage, DBModel
    
    if version is not None:
        db_package = DBPackage.from_name_version(name, version)
    else:
        db_package = DBPackage.from_name_latest(name)

    core.clear_functions(db_package.rowid)
    storage.package.remove(db_package.install_path)

    for model in DBModel.all_from_package(db_package.rowid):
        model.drop()
    db_package.drop()
    return {'status': 'OK'}
