from distutils.version import LooseVersion
from typing import Dict, Iterable

from hivemind_daemon import errors
import hivemind_daemon.package.db as db
from hivemind_daemon.server.json import HivemindEncoder


class DBPackage:
    create_table: str = (
        'CREATE TABLE package ('
        '   rowid INTEGER PRIMARY KEY AUTOINCREMENT,'
        '   name TEXT NOT NULL,'
        '   active INTEGER NOT NULL,'
        '   version TEXT,'
        '   humanname TEXT,'
        '   install_path TEXT NOT NULL,'
        '   UNIQUE (name, version)'
        ')'
    )

    def __init__(
            self,
            name: str,
            active: bool,
            version: str,
            human_name: str,
            install_path: str,
            rowid: int = None,
    ):
        self.name = name
        self.active = active
        self.version = version
        self.human_name = human_name
        self.install_path = install_path
        self.rowid = rowid
        
    @staticmethod
    def from_id(rowid: int) -> 'DBPackage':
        res = DBPackage(None, None, None, None, None, rowid=rowid)
        res.refresh()
        return res

    @staticmethod
    def from_name_version(name: str, version: str) -> 'DBPackage':
        with db.Cursor() as cur:
            cur.execute(
                'SELECT rowid, name, active, version, humanname, install_path'
                ' FROM package'
                ' WHERE name = ? AND version = ?',
                (name, version)
            )
            results = cur.fetchone()
        if results:
            rowid, name, active, version, human_name, install_path = results
            return DBPackage(name, bool(active), version, human_name, install_path, rowid)
        else:
            raise errors.DatabaseMissingEntry(f'Package {name}::{version} not found')

    @staticmethod
    def from_name_latest(name: str):
        with db.Cursor() as cur:
            cur.execute(
                'SELECT rowid, name, active, version, humanname, install_path'
                ' FROM package'
                ' WHERE name = ?',
                (name,)
            )
            # semver doesn't order nicely in sqlite, so we'll just grab everything and sort in python
            results = cur.fetchmany()
        if not results:
            raise errors.DatabaseMissingEntry(f'Package {name} not found')
        sort_key = lambda rowid, name, active, version, humanname, install_path: LooseVersion(version)
        try:
            latest_version = sorted(results, key=sort_key, reverse=True)[0]
        except TypeError:
            # LooseVersion didn't like comparing something in our list, indicating mixed or unparsable version strings
            # This might be kicking the can too far down the road
            # I could just declare 'VERSION SHALL BE SEMVER' and avoid this problem, but that loses flexibility
            latest_version = sorted(results, key=lambda x: x[3])[0]
        rowid, name, active, version, human_name, install_path = latest_version
        return DBPackage(name, bool(active), version, human_name, install_path, rowid)

    @staticmethod
    def get_all() -> Iterable['DBPackage']:
        with db.Cursor() as cur:
            cur.execute('SELECT rowid, name, active, version, humanname, install_path FROM package')
            results = cur.fetchone()
            while results:
                rowid, name, active, version, human_name, install_path = results
                yield DBPackage(name, bool(active), version, human_name, install_path, rowid)
                results = cur.fetchone()

    @staticmethod
    def get_active_packages() -> Iterable['DBPackage']:
        with db.Cursor() as cur:
            cur.execute(
                'SELECT rowid, name, active, version, humanname, install_path'
                ' FROM package'
                ' WHERE active = 1'
            )
            results = cur.fetchone()
            while results:
                rowid, name, active, version, human_name, install_path = results
                yield DBPackage(name, bool(active), version, human_name, install_path, rowid)
                results = cur.fetchone()
        
    def refresh(self):
        with db.Cursor() as cur:
            cur.execute(
                'SELECT name, active, version, humanname, install_path'
                ' FROM package'
                ' WHERE rowid = ?',
                (self.rowid,)
            )
            results = cur.fetchone()
        if results:
            self.name, self.active, self.version, self.human_name, self.install_path = results
        else:
            raise errors.DatabaseMissingEntry(f'Package at index {self.rowid} not found')

    def insert(self):
        if self.rowid is not None:
            raise errors.DatabaseError(f'Package {self.name} already exists at id {self.rowid}')
        self.active = int(bool(self.active))
        with db.Cursor() as cur:
            cur.execute(
                'INSERT INTO package (name, active, version, humanname, install_path) VALUES (?, ?, ?, ?, ?)',
                (self.name, self.active, self.version, self.human_name, self.install_path),
            )
            self.rowid = cur.lastrowid
        
    def upsert(self):
        if self.rowid is None:
            self.insert()
        else:
            self.update()

    def update(self):
        if self.rowid is None:
            raise errors.DatabaseError(f'Cannot update package {self.name} without an ID')
        self.active = int(bool(self.active))
        with db.Cursor() as cur:
            cur.execute(
                'UPDATE package SET name=?, active=?, version=?, humanname=?, install_path=? WHERE rowid = ?',
                (self.name, self.active, self.version, self.human_name, self.install_path, self.rowid),
            )
        
    def drop(self):
        if self.rowid is None:
            raise errors.DatabaseError(f'Cannot remove package {self.name} without an ID')
        with db.Cursor() as cur:
            cur.execute(
                'DELETE FROM package WHERE rowid = ?',
                (self.rowid,)
            )

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'active': self.active,
            'version': self.version,
            'human_name': self.human_name,
            'install_path': self.install_path,
            'id': self.rowid,
        }


class DBModel:
    create_table: str = (
        'CREATE TABLE model ('
        '   rowid INTEGER PRIMARY KEY AUTOINCREMENT,'
        '   package_id INTEGER NOT NULL,'
        '   name TEXT NOT NULL,'
        '   type TEXT NOT NULL,'
        '   install_path TEXT NOT NULL,'
        '   FOREIGN KEY (package_id) REFERENCES package(rowid),'
        '   UNIQUE (package_id, name)'
        ')'
    )

    def __init__(
            self,
            package_id: int,
            name: str,
            model_type: str,
            install_path: str,
            rowid: int = None,
    ):
        self.package_id = package_id
        self.name = name
        self.model_type = model_type
        self.install_path = install_path
        self.rowid = rowid

    @staticmethod
    def from_id_name(package_id: int, model_name: str) -> 'DBModel':
        with db.Cursor() as cur:
            cur.execute(
                'SELECT rowid, package_id, name, type, install_path'
                ' FROM model'
                ' WHERE package_id = ? AND name = ?',
                (package_id, model_name)
            )
            results = cur.fetchone()
        if results:
            rowid, package_id, name, model_type, install_path = results
            return DBModel(package_id, name, model_type, install_path, rowid)
        else:
            raise errors.DatabaseMissingEntry(f'Model {model_name} under package at index {package_id} not found')

    @staticmethod
    def from_names(package_name: str, model_name: str) -> 'DBModel':
        # Not guaranteed to be unique
        with db.Cursor() as cur:
            cur.execute(
                'SELECT model.rowid, model.package_id, model.name, model.type, model.install_path'
                ' FROM model INNER JOIN package ON model.package_id = package.rowid'
                ' WHERE package.name = ? AND model.name = ?',
                (package_name, model_name)
            )
            results = cur.fetchone()
        if results:
            rowid, package_id, name, model_type, install_path = results
            return DBModel(package_id, name, model_type, install_path, rowid)
        else:
            raise errors.DatabaseMissingEntry(f'Model {model_name} under package {package_name} not found')

    @staticmethod
    def all_from_package(package_id: int) -> Iterable['DBModel']:
        with db.Cursor() as cur:
            cur.execute(
                'SELECT rowid, package_id, name, type, install_path'
                ' FROM model'
                ' WHERE package_id = ?',
                (package_id,)
            )
            results = cur.fetchone()
            while results:
                rowid, package_id, name, model_type, install_path = results
                yield DBModel(package_id, name, model_type, install_path, rowid)
                results = cur.fetchone()

    def refresh(self):
        with db.Cursor() as cur:
            cur.execute(
                'SELECT package_id, name, type, install_path'
                ' FROM model'
                ' WHERE rowid = ?',
                (self.rowid,)
            )
            results = cur.fetchone()
        if results:
            self.package_id, self.name, self.model_type, self.install_path = results
        else:
            raise errors.DatabaseMissingEntry(f'Model at index {self.rowid} not found')

    def insert(self):
        if self.rowid is not None:
            raise errors.DatabaseError(f'Package {self.name} already exists at id {self.rowid}')
        with db.Cursor() as cur:
            cur.execute(
                'INSERT INTO model (package_id, name, type, install_path) VALUES (?, ?, ?, ?)',
                (self.package_id, self.name, self.model_type, self.install_path),
            )
            self.rowid = cur.lastrowid
        
    def upsert(self):
        if self.rowid is None:
            self.insert()
        else:
            self.update()

    def update(self):
        if self.rowid is None:
            raise errors.DatabaseError(f'Cannot update model {self.name} without an ID')
        with db.Cursor() as cur:
            cur.execute(
                'UPDATE model SET package_id=?, name=?, type=?, install_path=? WHERE rowid = ?',
                (self.package_id, self.name, self.model_type, self.install_path, self.rowid),
            )

    def drop(self):
        if self.rowid is None:
            raise errors.DatabaseError(f'Cannot remove model {self.name} without an ID')
        with db.Cursor() as cur:
            cur.execute(
                'DELETE FROM model WHERE rowid = ?',
                (self.rowid,)
            )

    def to_dict(self) -> Dict:
        return {
            'package_id': self.package_id,
            'name': self.name,
            'model_type': self.model_type,
            'install_path': self.install_path,
            'id': self.rowid,
        }


HivemindEncoder.register_encoder(DBPackage, lambda x: x.to_dict())
HivemindEncoder.register_encoder(DBModel, lambda x: x.to_dict())
