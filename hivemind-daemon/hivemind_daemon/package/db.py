import os
import sqlite3
from typing import Dict, Iterable
import threading

from hivemind_daemon import errors, storage
from hivemind_daemon.package.orm import DBPackage, DBModel


connection_pool = threading.local()
connection_pool.conn = None


def _db_path():
    return os.path.join(storage.root_path, 'package.db')


def get_conn():
    if getattr(connection_pool, 'conn', None) is None:
        connection_pool.conn = sqlite3.connect(_db_path())
    return connection_pool.conn


def init_db():
    if not os.path.exists(_db_path()):
        _init_db()

        
def _init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(DBPackage.create_table)
    cur.execute(DBModel.create_table)
    cur.close()
    conn.commit()


def install_package(package: Dict, install_id: str) -> DBPackage:
    # TODO check for package install conflicts first
    # E.g. version, etc
    conn = get_conn()

    db_package = DBPackage(
        name=package['name'],
        active=False,
        version=package.get('version', None),
        human_name=package.get('humanname', None),
        install_path=install_id,
    )
    db_package.insert()

    for model_name, model_spec in package['model'].items():
        install_path = os.path.join(install_id, f'{model_name}.{model_spec["type"]}')
        model = DBModel(
            package_id=db_package.rowid,
            name=model_name, 
            model_type=model_spec['type'], 
            install_path=install_path
        )
        model.insert()

    conn.commit()

    return db_package


def get_model(package_name: str, model_name: str) -> str:
    fname = os.path.join(storage.model_path, package_name, f'{model_name}.onnx')
    if not os.path.isfile(fname):
        raise errors.InternalError(f'Model for {model_name} was missing from cache')
    return fname
