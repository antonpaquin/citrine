from typing import *

import hivemind_client
from PySide2 import QtCore
from PySide2.QtCore import Qt

from hivemind_ui import errors, app
from hivemind_ui.util import threaded
from hivemind_ui.config import get_config


class SearchPackage(QtCore.QObject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.on_remove = None

    @threaded
    def install(self):
        progress_list = ProgressList.get_instance()
        if self.on_remove is not None:
            self.on_remove()
        progress_list.install_package(self.name)

        
class ProgressPackage(QtCore.QObject):
    sig_updated: QtCore.SignalInstance = QtCore.Signal()
    
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.value = 0
        self.maximum = 1
        self.on_remove = None
        
    def update(self, data: Dict):
        if 'download-progress' not in data or 'download-size' not in data:
            return
        self.value = data['download-progress']
        self.maximum = data['download-size']
        self.sig_updated.emit()

    @threaded
    def finish(self):
        if self.on_remove is not None:
            self.on_remove()
        installed_list = InstalledList.get_instance()
        installed_list.refresh()

        
class InstalledPackage(QtCore.QObject):
    sig_updated: QtCore.SignalInstance = QtCore.Signal()
    sig_removed: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self, name: str, human_name: str, version: str, active: bool):
        super().__init__()
        self.name = name
        self.human_name = human_name
        self.version = version
        self.active = active
        self.on_remove = None

    @threaded
    def active_toggle(self):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        try:
            if self.active:
                client.deactivate(self.name, self.version)
                self.active = False
            else:
                client.activate(self.name, self.version)
                self.active = True
        except errors.HivemindError as e:
            app.display_error(e)
        self.sig_updated.emit()

    @threaded
    def remove(self):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        try:
            pass
            client.remove(self.name, self.version)
        except errors.HivemindError as e:
            app.display_error(e)
            return
        if self.on_remove is not None:
            self.on_remove()
        self.sig_removed.emit()
        

class SearchList(QtCore.QObject):
    _instance = None

    sig_data_changed: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.packages = []  # type: List[SearchPackage]

    @staticmethod
    def get_instance() -> 'SearchList':
        if SearchList._instance is None:
            SearchList._instance = SearchList()
        return SearchList._instance

    @threaded
    def query_packages(self, query: str):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        try:
            search_packages = client.search(query=query)['packages']
            installed_packages = client.list()['packages']
        except hivemind_client.errors.HivemindClientError as e:
            app.display_error(e)
            return

        installed_names = [pkg['name'] for pkg in installed_packages]
        missing_packages = [name for name in search_packages if name not in installed_names]
        self.packages = []
        for name in missing_packages:
            pkg = SearchPackage(name)
            pkg.on_remove = lambda: self.remove(pkg)
            self.packages.append(pkg)
        self.sig_data_changed.emit()
        
    def remove(self, package: SearchPackage):
        self.packages.remove(package)
        self.sig_data_changed.emit()
        

class ProgressList(QtCore.QObject):
    _instance = None

    sig_data_changed: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.packages = []  # type: List[ProgressPackage]

    @staticmethod
    def get_instance() -> 'ProgressList':
        if ProgressList._instance is None:
            ProgressList._instance = ProgressList()
        return ProgressList._instance

    @threaded
    def install_package(self, name: str):
        pkg = ProgressPackage(name)
        pkg.on_remove = lambda: self.finished(pkg)
        self.packages.append(pkg)
        self.sig_data_changed.emit()
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'), async_=True)
        try:
            client.install(name, progress_callback=pkg.update)
        except hivemind_client.errors.HivemindClientError as e:
            app.display_error(e)
            return
        pkg.finish()

    def finished(self, package: ProgressPackage):
        self.packages.remove(package)
        self.sig_data_changed.emit()
        
        
class InstalledList(QtCore.QObject):
    _instance = None

    sig_data_changed: QtCore.SignalInstance = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.packages = []  # type: List[InstalledPackage]

    @staticmethod
    def get_instance() -> 'InstalledList':
        if InstalledList._instance is None:
            InstalledList._instance = InstalledList()
        return InstalledList._instance
    
    @threaded
    def refresh(self):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        try:
            package_list = client.list()
        except hivemind_client.errors.HivemindClientError as e:
            app.display_error(e)
            return

        li = []
        for package in package_list['packages']:
            model = InstalledPackage(
                name=package['name'],
                human_name=package['human_name'],
                version=package['version'],
                active=package['active'],
            )
            model.on_remove = lambda: self.remove(model)
            model.sig_removed.connect(self.sig_data_changed.emit, type=Qt.QueuedConnection)
            li.append(model)

        self.packages = li
        self.sig_data_changed.emit()
        
    def remove(self, installed_package: InstalledPackage):
        self.packages.remove(installed_package)
        self.refresh()
