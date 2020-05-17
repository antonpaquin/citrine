import importlib.util
import json
import os
import threading
from typing import Dict, Any, Optional

import cerberus

import hivemind_daemon.package.db as db
from hivemind_daemon import storage, errors


package_validator = {
    'name': {
        'type': 'string',
        'required': True,
        'minlength': 1,
    },
    'module': {
        'type': 'string',
        'required': True,
    },
    'model': {
        'type': 'dict',
        'keysrules': {
            'type': 'string',
        },
        'valuesrules': {
            'type': 'dict',
            'schema': {
                'type': {
                    'type': 'string',
                    'required': True,
                    'allowed': ['onnx'],
                },
                'file': {
                    'type': 'string',
                    'required': True,
                },
            },
        },
    },
    'humanname': {
        'type': 'string',
        'required': False,
    },
    'version': {
        'type': 'string',
        'required': False,
    },
}


load_context = {'package_id': None}  # type: Dict[str, Optional[Any]]
load_context_lock = threading.Lock()


def load_package_json(name):
    with open(name, 'r') as in_f:
        jsn = json.load(in_f)

    v = cerberus.Validator(schema=package_validator)
    if not v.validate(jsn):
        raise errors.PackageInstallError(f'Improperly formatted package.json', data=v.errors)

    return v.document


def get_loading_package_id():
    if not load_context_lock.locked():
        raise errors.InternalError('No package is currently loading')
    return


def init_packages():
    for db_package in db.DBPackage.get_active_packages():
        load_package(db_package)
        
        
def activate_package(name: str, version: str):
    db_package = db.DBPackage.from_name_version(name, version)
    _activate_package(db_package)


def _activate_package(db_package: db.DBPackage):
    if db_package.rowid is None:
        raise errors.InternalError('Tried to activate a package not in the database', data=db_package.to_dict())
    load_package(db_package)

    conn = db.get_conn()
    db_package.active = True
    db_package.update()
    conn.commit()
    

class PackageContext(object):
    def __init__(self, package_id: int):
        self.package_id = package_id

    def __enter__(self):
        load_context_lock.acquire()
        load_context['package_id'] = self.package_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        load_context['package_id'] = None
        load_context_lock.release()


def load_package(db_package: db.DBPackage):
    module_file = storage.get_package_module(db_package)

    # I dunno where this actually shows up, but it's not a problem yet. Maybe multiple imports?
    useless_module_name = 'userpackage'
    spec = importlib.util.spec_from_file_location(useless_module_name, module_file)
    mod = importlib.util.module_from_spec(spec)
    try:
        with PackageContext(package_id=db_package.rowid):
            spec.loader.exec_module(mod)
    except errors.HivemindException:
        raise
    except Exception as e:
        raise errors.PackageInstallError(f'Failed to load module for package {db_package.name}', data=str(e))


