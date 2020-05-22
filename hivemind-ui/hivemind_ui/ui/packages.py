import json
import os
import threading
from typing import *

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt

import hivemind_client

from hivemind_ui import app
from hivemind_ui.config import get_config
from hivemind_ui.qt_util import HBox, VBox, NavButton, qt_xml, threaded


class DaemonPackage(QtCore.QObject):

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
        if self.active:
            client.deactivate(self.name, self.version)
            self.active = False
        else:
            client.activate(self.name, self.version)
            self.active = True
        self.sig_updated.emit()

    @threaded
    def remove(self):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        client.remove(self.name, self.version)
        if self.on_remove is not None:
            self.on_remove()
        self.sig_removed.emit()


class PackageInProgress(QtCore.QObject):

    sig_update_progress: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.value = 0
        self.maximum = 1

    def update(self, data: Dict):
        if 'download-progress' not in data or 'download-size' not in data:
            return
        self.value = data['download-progress']
        self.maximum = data['download-size']
        self.sig_update_progress.emit()


class PackagesModel(QtCore.QObject):
    _instance = None

    sig_changed_packages: QtCore.SignalInstance = QtCore.Signal()
    sig_error: QtCore.SignalInstance = QtCore.Signal(str)

    def __init__(self):
        super().__init__(parent=app.get_root())
        self.packages = []
        self.in_progress_packages = []

    @staticmethod
    def get_instance() -> 'PackagesModel':
        if PackagesModel._instance is None:
            PackagesModel._instance = PackagesModel()
        return PackagesModel._instance

    @threaded
    def query_packages(self):
        client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        try:
            package_list = client.list()
        except hivemind_client.errors.HivemindClientError as e:
            self.sig_error.emit(json.dumps(e.to_dict(), indent=4))
            return

        li = []
        for package in package_list['packages']:
            model = DaemonPackage(
                name=package['name'],
                human_name=package['human_name'],
                version=package['version'],
                active=package['active'],
            )
            model.on_remove = lambda: self.packages.remove(model)
            model.sig_removed.connect(self.sig_changed_packages.emit)
            li.append(model)

        self.packages = li
        self.sig_changed_packages.emit()

    def install_package(self, fname: str) -> PackageInProgress:
        in_progress = PackageInProgress(os.path.basename(fname))

        def install_package_thread():
            self.in_progress_packages.append(in_progress)
            self.sig_changed_packages.emit()
            client = hivemind_client.api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
            try:
                client.install(specfile=fname, progress_callback=in_progress.update)
            except hivemind_client.errors.HivemindClientError as e:
                self.sig_error.emit(json.dumps(e.to_dict(), indent=4))
            self.in_progress_packages.remove(in_progress)
            self.query_packages()

        t = threading.Thread(target=install_package_thread)
        t.start()

        return in_progress


@qt_xml.register('PackagePageHeader')
class PackagePageHeader(HBox): pass


@qt_xml.register('PackageProgress')
class PackageProgress(HBox):
    name_label: QtWidgets.QLabel
    progress_bar: QtWidgets.QProgressBar

    def __init__(self, model: PackageInProgress):
        super().__init__()
        self.load_xml('PackageProgress.xml')
        self.model = model
        self.model.sig_update_progress.connect(self.update_progress)
        self.name_label.setText(model.name)

    def update_progress(self):
        self.progress_bar.setValue(self.model.value)
        self.progress_bar.setMaximum(self.model.maximum)


@qt_xml.register('PackageEntry')
class PackageEntry(HBox):
    human_name: QtWidgets.QLabel
    name: QtWidgets.QLabel
    version: QtWidgets.QLabel
    active_btn: QtWidgets.QPushButton
    remove_btn: QtWidgets.QPushButton

    def __init__(self, model: DaemonPackage):
        super().__init__()
        self.load_xml('PackageEntry.xml')

        self.model = model
        self.model.sig_updated.connect(self.update)
        self.update()

        self.active_btn.mousePressEvent = self.active_toggle
        self.remove_btn.mousePressEvent = self.remove

    def update(self):
        self.name.setText(self.model.name)
        self.human_name.setText(self.model.human_name)
        self.version.setText(self.model.version)
        self.active_btn.setText('deactivate' if self.model.active else 'activate')

    def active_toggle(self, ev: QtCore.QEvent):
        self.model.active_toggle()

    def remove(self, ev: QtCore.QEvent):
        self.model.remove()


@qt_xml.register('PackagePage')
class PackagePage(VBox):
    li: QtWidgets.QListWidget
    label_filename: QtWidgets.QLabel
    dialog_btn: QtWidgets.QPushButton

    def __init__(self):
        super().__init__()
        self.load_xml('PackagePage.xml')

        self.model = PackagesModel.get_instance()
        self.model.sig_changed_packages.connect(self.populate)
        self.model.sig_error.connect(self.show_err)
        self.populate()
        self.model.query_packages()

        self.dialog_btn.mousePressEvent = self.pick_file

        self.show()

    def pick_file(self, event: QtCore.QEvent):
        fname = QtWidgets.QFileDialog.getOpenFileName()[0]
        if not fname:
            return
        self.model.install_package(fname)

    def show_err(self, err: str):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(err)
        msg_box.exec()

    def populate(self):
        items = []
        for in_progress_model in self.model.in_progress_packages:
            list_item = QtWidgets.QListWidgetItem()
            list_item.setFlags(Qt.ItemIsSelectable)
            in_progress_entry = PackageProgress(in_progress_model)
            items.append((list_item, in_progress_entry))

        for package_model in self.model.packages:
            package_entry = PackageEntry(package_model)
            list_item = QtWidgets.QListWidgetItem()
            list_item.setFlags(Qt.ItemIsSelectable)
            items.append((list_item, package_entry))

        self.li.clear()
        for list_item, widget in items:
            self.li.addItem(list_item)
            self.li.setItemWidget(list_item, widget)


@qt_xml.register('PackageNavButton')
class PackageNavButton(NavButton):
    text = 'packages'
    panel_class = PackagePage
