from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import Qt

from citrine_ui.qt_util import HBox, VBox, NavButton, register_xml

from . import models


@register_xml('PackagePageHeader')
class PackagePageHeader(HBox): pass


@register_xml('SearchPackage')
class SearchPackage(HBox):
    name_label: QtWidgets.QLabel
    install_btn: QtWidgets.QPushButton

    def __init__(self, model: models.SearchPackage):
        super().__init__()
        self.load_xml('SearchPackage.xml')
        self.model = model
        self.name_label.setText(self.model.name)
        self.install_btn.mousePressEvent = self.click_install
        
    def click_install(self, _: QtGui.QMouseEvent):
        self.model.install()
        
        
@register_xml('ProgressPackage')
class ProgressPackage(HBox):
    name_label: QtWidgets.QLabel
    progress_bar: QtWidgets.QProgressBar

    def __init__(self, model: models.ProgressPackage):
        super().__init__()
        self.load_xml('ProgressPackage.xml')
        self.model = model
        self.model.sig_updated.connect(self.update_progress, type=Qt.QueuedConnection)
        self.name_label.setText(model.name)

    def update_progress(self):
        self.progress_bar.setValue(self.model.value)
        self.progress_bar.setMaximum(self.model.maximum)


@register_xml('InstalledPackage')
class InstalledPackage(HBox):
    human_name: QtWidgets.QLabel
    name: QtWidgets.QLabel
    version: QtWidgets.QLabel
    active_btn: QtWidgets.QPushButton
    remove_btn: QtWidgets.QPushButton

    def __init__(self, model: models.InstalledPackage):
        super().__init__()
        self.load_xml('InstalledPackage.xml')
        self.model = model
        self.model.sig_updated.connect(self.update, type=Qt.QueuedConnection)
        self.active_btn.mousePressEvent = self.active_toggle
        self.remove_btn.mousePressEvent = self.remove
        self.update()

    def update(self):
        self.name.setText(self.model.name)
        self.human_name.setText(self.model.human_name)
        self.version.setText(self.model.version)
        self.active_btn.setText('deactivate' if self.model.active else 'activate')
        
    def active_toggle(self, _: QtGui.QMouseEvent):
        self.model.active_toggle()
        
    def remove(self, _: QtGui.QMouseEvent):
        self.model.remove()


@register_xml('PackageSearchList')
class PackageSearchList(QtWidgets.QListWidget):
    def __init__(self, model: models.SearchList):
        super().__init__()
        self.model = model
        self.model.sig_data_changed.connect(self.refresh)
        
    def refresh(self):
        self.clear()
        for search_package in self.model.packages:
            widget = SearchPackage(search_package)
            wrapper = QtWidgets.QListWidgetItem()
            wrapper.setFlags(Qt.ItemIsSelectable)
            self.addItem(wrapper)
            self.setItemWidget(wrapper, widget)
        if self.count() == 0:
            self.setHidden(True)
            self.sizePolicy().setVerticalStretch(0)
        else:
            self.setHidden(False)
            self.sizePolicy().setVerticalStretch(1)


@register_xml('PackageProgressList')
class PackageProgressList(QtWidgets.QListWidget):
    def __init__(self, model: models.ProgressList):
        super().__init__()
        self.model = model
        self.model.sig_data_changed.connect(self.refresh)

    def refresh(self):
        self.clear()
        for progress_package in self.model.packages:
            widget = ProgressPackage(progress_package)
            wrapper = QtWidgets.QListWidgetItem()
            wrapper.setFlags(Qt.ItemIsSelectable)
            self.addItem(wrapper)
            self.setItemWidget(wrapper, widget)
        if self.count() == 0:
            self.setHidden(True)
            self.sizePolicy().setVerticalStretch(0)
        else:
            self.setHidden(False)
            self.sizePolicy().setVerticalStretch(1)


@register_xml('PackageInstalledList')
class PackageInstalledList(QtWidgets.QListWidget):
    def __init__(self, model: models.InstalledList):
        super().__init__()
        self.model = model
        self.model.sig_data_changed.connect(self.refresh)

    def refresh(self):
        self.clear()
        for installed_package in self.model.packages:
            widget = InstalledPackage(installed_package)
            wrapper = QtWidgets.QListWidgetItem()
            wrapper.setFlags(Qt.ItemIsSelectable)
            self.addItem(wrapper)
            self.setItemWidget(wrapper, widget)
        if self.count() == 0:
            self.setHidden(True)
            self.sizePolicy().setVerticalStretch(0)
        else:
            self.setHidden(False)
            self.sizePolicy().setVerticalStretch(1)


@register_xml('PackagePage')
class PackagePage(VBox):
    li_search: PackageSearchList
    li_progress: PackageProgressList
    li_installed: PackageInstalledList
    search_bar: QtWidgets.QLineEdit

    def __init__(self):
        super().__init__()
        self.load_xml('PackagePage.xml')

        self.li_search = PackageSearchList(models.SearchList.get_instance())
        self.li_progress = PackageProgressList(models.ProgressList.get_instance())
        self.li_installed = PackageInstalledList(models.InstalledList.get_instance())

        self.addWidget(self.li_progress)
        self.addWidget(self.li_search)
        self.addWidget(self.li_installed)
        
        self.li_search.model.query_packages('')
        self.li_progress.refresh()
        self.li_installed.model.refresh()

        self.search_bar.textChanged.connect(self.edit_search, type=Qt.QueuedConnection)
        
    def edit_search(self, ev: QtCore.QEvent):
        self.li_search.model.query_packages(self.search_bar.text())


@register_xml('PackageNavButton')
class PackageNavButton(NavButton):
    text = 'packages'
    panel_class = PackagePage
