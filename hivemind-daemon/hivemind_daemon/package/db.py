import os
import sqlite3
from typing import *
import threading

from hivemind_daemon import errors, storage
from hivemind_daemon.package.orm import DBPackage, DBModel


connection_pool = threading.local()
connection_pool.conn = None


def _db_path():
    return os.path.join(storage.root_path, 'package.db')


def start_connection():
    connection_pool.conn = sqlite3.connect(_db_path())
    
    
def end_connection(commit: bool):
    conn = connection_pool.conn  # type: sqlite3.Connection
    if commit:
        conn.commit()
    else:
        conn.rollback()
    conn.close()
    connection_pool.conn = None


def get_conn():
    if getattr(connection_pool, 'conn', None) is None:
        # TODO: I kinda only want this to work on the main thread
        # worker threads should have something available via start_connection()
        connection_pool.conn = sqlite3.connect(_db_path())
    return connection_pool.conn


class Cursor:
    def __init__(self, conn=None):
        if conn:
            self.conn = conn
        else:
            self.conn = None
        self.cur = None
        
    def __enter__(self):
        if self.conn is None:
            self.conn = connection_pool.conn
        self.cur = self.conn.cursor()
        return self.cur
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()


def init_db():
    if not os.path.exists(_db_path()):
        _init_db()

        
def _init_db():
    conn = get_conn()
    with Cursor(conn) as cur:
        cur.execute(DBPackage.create_table)
        cur.execute(DBModel.create_table)
    conn.commit()


def install_package(package_meta: Dict, install_id: str) -> DBPackage:
    try:
        db_package = DBPackage(
            name=package_meta['name'],
            active=False,
            version=package_meta.get('version', None),
            human_name=package_meta.get('humanname', None),
            install_path=install_id,
        )
        db_package.insert()
    except sqlite3.IntegrityError as e:
        raise errors.PackageInstallError(f'Package {package_meta["name"]} already exists', data=str(e))

    for model_name, model_spec in package_meta['model'].items():
        install_path = os.path.join(install_id, f'{model_name}.{model_spec["type"]}')
        model = DBModel(
            package_id=db_package.rowid,
            name=model_name, 
            model_type=model_spec['type'], 
            install_path=install_path
        )
        model.insert()

    return db_package


def list_packages() -> Dict:
    return {
        'packages': list(DBPackage.get_all())
    }

