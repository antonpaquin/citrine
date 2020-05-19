import os
import shutil
import tempfile
from typing import Optional, Dict
import uuid
import zipfile

from hivemind_daemon import errors, storage
import hivemind_daemon.package.db as db
from hivemind_daemon.package.load import _set_package_active, load_package_json


def install_package_file(localfile: str, activate: bool) -> Dict:
    # The cross-package complexity of this is a little annoying
    # Take advantage of opportunities to simplify

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

        package_meta = load_package_json(os.path.join(tmpdir, 'package.json'))
        install_id = str(uuid.uuid4())
        db_package = db.install_package(package_meta, install_id)
        storage.package.install_from_temp(tmpdir, install_id, package_meta)

    if activate:
        _set_package_active(db_package, True)

    return {'status': 'OK'}


def install_package_url(url: str, package_hash: str, activate: bool) -> Dict:
    dl_file = storage.download.get_file(url, package_hash)
    return install_package_file(dl_file, activate)


def remove_package(name: str, version: Optional[str]):
    if version is not None:
        db_package = db.DBPackage.from_name_version(name, version)
    else:
        db_package = db.DBPackage.from_name_latest(name)

    storage.package.remove(db_package.install_path)

    for model in db.DBModel.all_from_package(db_package.rowid):
        model.drop()
    db_package.drop()
    return {'status': 'OK'}
