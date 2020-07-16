import importlib.util
import json
import logging
import os
import threading
from typing import Dict, Any, Optional

import cerberus

from citrine_daemon import storage, errors, package, core
from citrine_daemon.package import db


logger = logging.getLogger(__name__)

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


load_context = {'package': None}  # type: Dict[str, Optional[Any]]
load_context_lock = threading.Lock()


def load_package_meta(name):
    with open(name, 'r') as in_f:
        jsn = json.load(in_f)

    v = cerberus.Validator(schema=package_validator)
    if not v.validate(jsn):
        raise errors.PackageInstallError(f'Improperly formatted meta.json', data=v.errors)

    return v.document


def get_loading_package() -> Optional[db.DBPackage]:
    if not load_context_lock.locked():
        return None
    return load_context['package']


def init_packages():
    logger.info('Loading existing packages on startup')
    package.db.get_conn()
    for db_package in db.DBPackage.get_active_packages():
        load_package(db_package)
        
        
def activate_package(name: str, version: Optional[str]):
    logger.info(f'Setting package {name}v{version} to active', {'package_name': name, 'package_version': version})
    # TODO enforce only one active
    # only one version of a package with a given name should be active at a time
    if version is not None:
        db_package = db.DBPackage.from_name_version(name, version)
    else:
        db_package = db.DBPackage.from_name_latest(name)
    set_package_active(db_package, True)
    return {'status': 'OK'}


def deactivate_package(name: str, version: Optional[str]):
    logger.info(f'Setting package {name}v{version} to inactive', {'package_name': name, 'package_version': version})
    if version is not None:
        db_package = db.DBPackage.from_name_version(name, version)
    else:
        db_package = db.DBPackage.from_name_latest(name)
    set_package_active(db_package, False)
    core.clear_functions(db_package.rowid)
    return {'status': 'OK'}


def set_package_active(db_package: db.DBPackage, active: bool):
    if db_package.rowid is None:
        raise errors.InternalError('Tried to activate a package not in the database', data=db_package.to_dict())
    load_package(db_package)

    db_package.active = active
    db_package.update()


class PackageContext(object):
    def __init__(self, pkg: db.DBPackage):
        self.package = pkg

    def __enter__(self):
        load_context_lock.acquire()
        load_context['package'] = self.package

    def __exit__(self, exc_type, exc_val, exc_tb):
        load_context['package'] = None
        load_context_lock.release()


def load_package(db_package: db.DBPackage):
    log_ctx = {'package_name': db_package.name, 'package_version': db_package.version}
    logger.info('Beginning to load package module', log_ctx)
    module_file = storage.get_package_module(db_package)

    # I dunno where this actually shows up, but it's not a problem yet. Maybe multiple imports?
    useless_module_name = 'userpackage'
    spec = importlib.util.spec_from_file_location(useless_module_name, module_file)
    mod = importlib.util.module_from_spec(spec)
    
    work_dir = os.getcwd()
    exec_dir = os.path.join(storage.package_path(), db_package.install_path)
    try:
        os.chdir(exec_dir)
        with PackageContext(db_package):
            logger.info('BEGIN loading module', log_ctx)
            spec.loader.exec_module(mod)
            logger.info('END loading module', log_ctx)
    except errors.CitrineException:
        raise
    except Exception as e:
        logger.warning('FAIL loading module', log_ctx)
        raise errors.PackageInstallError(f'Failed to load module for package {db_package.name}', data=str(e))
    finally:
        os.chdir(work_dir)

