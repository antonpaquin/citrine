import logging
import os
import sqlite3
from typing import *
import threading

from hivemind_daemon import errors, storage
from hivemind_daemon.package.orm import DBPackage, DBModel


connection_pool = threading.local()
connection_pool.conn = None

package_endpoints = {}  # type: Dict[int, List[str]]

logger = logging.getLogger(__name__)


def _db_path():
    logger.debug('Initializing DB connection')
    return os.path.join(storage.root_path(), 'package.db')


def start_connection():
    connection_pool.conn = sqlite3.connect(_db_path())
    
    
def end_connection(commit: bool):
    conn = connection_pool.conn  # type: sqlite3.Connection
    if commit:
        logger.debug('Request completed successfully, will commit outstanding DB transactions')
        conn.commit()
    else:
        logger.info('Request failed, rolling back database')
        conn.rollback()
    conn.close()
    connection_pool.conn = None


def get_conn():
    if getattr(connection_pool, 'conn', None) is None:
        # TODO: I kinda only want this to work on the main thread
        # worker threads should have something available via start_connection()
        connection_pool.conn = sqlite3.connect(_db_path())
    return connection_pool.conn


def mark_package_endpoint(package_id: int, endpoint: str):
    # Transient and populated as packages are loaded and create their endpoints
    # This isn't used for anything internal, it's just for showing what endpoints a package owns under /package/list
    if package_id not in package_endpoints:
        package_endpoints[package_id] = []
    package_endpoints[package_id].append(endpoint)


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
    logger.info('Creating new Hivemind Database')
    conn = get_conn()
    with Cursor(conn) as cur:
        cur.execute(DBPackage.create_table)
        cur.execute(DBModel.create_table)
    conn.commit()


def install_package(package_meta: Dict, install_id: str) -> DBPackage:
    logger.info('Installing new package to database', {
        'package_name': package_meta['name'],
        'package_version': package_meta['version'],
    })
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
        logger.warning('Database rejected package installation')
        raise errors.PackageInstallError(f'Package {package_meta["name"]} already exists', data=str(e))

    for model_name, model_spec in package_meta['model'].items():
        logger.info(f'Installing model {model_name} for package {package_meta["name"]}', {
            'package_name': package_meta['name'],
            'package_version': package_meta['version'],
            'model_name': model_name,
        })
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
    packages = []
    for pkg in DBPackage.get_all():
        entry = pkg.to_dict()
        if pkg.rowid in package_endpoints:
            entry['endpoints'] = package_endpoints[pkg.rowid]
        packages.append(entry)
    return {'packages': packages}

