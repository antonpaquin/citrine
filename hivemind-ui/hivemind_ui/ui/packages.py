import os

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt

from hivemind_client import api

from hivemind_ui.config import get_config
from hivemind_ui.qt_util import HBox, VBox, NavButton, qt_xml


@qt_xml.register('PackagePageHeader')
class PackagePageHeader(HBox): pass


@qt_xml.register('PackageProgress')
class PackageProgress(HBox):
    name_label: QtWidgets.QLabel
    progress_bar: QtWidgets.QProgressBar

    def __init__(self, fname: str):
        super().__init__()
        self.load_xml('PackageProgress.xml')
        self.fname = fname
        self.name_label.setText(os.path.basename(fname))
        
    def update_progress(self, data):
        if 'download-progress' not in data or 'download-size' not in data:
            return
        self.progress_bar.setMaximum(data['download-size'])
        self.progress_bar.setValue(data['download-progress'])


@qt_xml.register('PackageEntry')
class PackageEntry(HBox):
    human_name: QtWidgets.QLabel
    name: QtWidgets.QLabel
    version: QtWidgets.QLabel
    active_btn: QtWidgets.QPushButton
    remove_btn: QtWidgets.QPushButton
    
    def __init__(self, page: 'PackagePage', name: str, human_name: str, version: str, active: bool):
        super().__init__()
        self.load_xml('PackageEntry.xml')
        
        self._page = page
        self._name = name
        self._human_name = human_name
        self._version = version
        self._active = active
        
        self.name.setText(name)
        self.human_name.setText(human_name)
        self.version.setText(version)
        self.active_btn.setText('deactivate' if active else 'activate')

        self.active_btn.mousePressEvent = self.active_toggle
        self.remove_btn.mousePressEvent = self.remove
        
    def active_toggle(self, event: QtCore.QEvent):
        client = api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        if self._active:
            client.deactivate(self._name, self._version)
            self.active_btn.setText('activate')
            self._active = False
        else:
            client.activate(self._name, self._version)
            self.active_btn.setText('deactivate')
            self._active = True
            
    def remove(self, event: QtCore.QEvent):
        client = api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        client.remove(self._name, self._version)
        self._page.populate()
        

@qt_xml.register('PackagePage')
class PackagePage(VBox):
    li: QtWidgets.QListWidget
    label_filename: QtWidgets.QLabel
    dialog_btn: QtWidgets.QPushButton

    def __init__(self):
        super().__init__()
        self.load_xml('PackagePage.xml')

        self._in_progress = []

        self.dialog_btn.mousePressEvent = self.pick_file

        self.populate()
        self.show()
        
    def pick_file(self, event: QtCore.QEvent):
        def pick_file_thread():
            fname = QtWidgets.QFileDialog.getOpenFileName()[0]
            if not fname:
                return
            client = api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
            progress_entry = PackageProgress(fname)
            self._in_progress.append(progress_entry)
            self.populate()
            client.install(specfile=fname, progress_callback=progress_entry.update_progress)
            self._in_progress.remove(progress_entry)
            self.populate()
        # So, QT freaks the hell out if this stuff happens outside a "QThread"
        # QtCore.QThread
        # And it also destroys the QThread if it falls out of scope here,
        # and subsequently segfaults.
        # Need to set up a proper worker / job pool towards the start, which is annoying
        # and not lightweight enough to just do here

        # Also, probably want to expose any error that might come up

        # Actually this qthread stuff probably needs to happen for _all_ of these network calls, plus
        # maybe some more in other pages.

        # And I probably also want to synchronize the things with appropriate locks.
        
        # Fun...

    def populate(self):
        client = api.PackageClient(get_config('daemon.server'), get_config('daemon.port'))
        package_list = client.list()
        self.li.clear()

        for progress_entry in self._in_progress:
            list_item = QtWidgets.QListWidgetItem()
            list_item.setFlags(Qt.ItemIsSelectable)
            self.li.addItem(list_item)
            self.li.setItemWidget(list_item, progress_entry)

        for package in package_list['packages']:
            entry = PackageEntry(
                self,
                name=package['name'],
                human_name=package['human_name'],
                version=package['version'],
                active=package['active'],
            )
            list_item = QtWidgets.QListWidgetItem()
            list_item.setFlags(Qt.ItemIsSelectable)
            self.li.addItem(list_item)
            self.li.setItemWidget(list_item, entry)


@qt_xml.register('PackageNavButton')
class PackageNavButton(NavButton):
    text = 'packages'
    panel_class = PackagePage
