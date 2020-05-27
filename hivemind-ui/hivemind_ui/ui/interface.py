from typing import *

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtCore
from PySide2 import QtWebEngineWidgets

from hivemind_ui import app, interface_pkg, js_bridge, errors
from hivemind_ui.qt_util import HBox, VBox, NavButton, XDialog, register_xml
from hivemind_ui.util import threaded


class InterfaceSelectorModel(QtCore.QObject):
    _instance: 'InterfaceSelectorModel' = None

    interfaces_updated: QtCore.SignalInstance = QtCore.Signal()
    available_interfaces_updated: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self):
        super().__init__(parent=app.get_root())

        self.interfaces = {}  # type: Dict[str, interface_pkg.Interface]
        self.available_interfaces = []

    @staticmethod
    def get_instance() -> 'InterfaceSelectorModel':
        if InterfaceSelectorModel._instance is None:
            InterfaceSelectorModel._instance = InterfaceSelectorModel()
        return InterfaceSelectorModel._instance

    @threaded
    def synchronize(self):
        try:
            interface_pkg.synchronize()
        except errors.HivemindError as e:
            app.display_error(e)
        self._refresh()

    @threaded
    def refresh(self):
        self._refresh()

    def _refresh(self):
        try:
            interfaces = interface_pkg.list_interfaces()
        except errors.HivemindError as e:
            app.display_error(e)
            return
        self.interfaces = {interface.name: interface for interface in interfaces}
        self.interfaces_updated.emit()

    @threaded
    def update_available(self):
        try:
            self.available_interfaces = interface_pkg.list_available_interfaces()
        except errors.HivemindError as e:
            app.display_error(e)
            return
        self.available_interfaces_updated.emit()
        
    def is_installed(self, interface_name: str) -> bool:
        return interface_name in self.interfaces
    
    @threaded
    def modify_interfaces(self, add_interfaces: List[str], remove_interfaces: List[str]):
        try:
            for interface_name in add_interfaces:
                interface_pkg.install_interface(interface_name)
            for interface_name in remove_interfaces:
                interface_pkg.remove_interface(interface_name)
        except errors.HivemindError as e:
            app.display_error(e)
        self._refresh()


class InterfaceViewEntry(QtWidgets.QTreeWidgetItem):
    def __init__(self, view: interface_pkg.InterfaceView):
        super().__init__()
        self.setText(0, view.name)
        self.view = view


class InterfaceWebPage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.view: interface_pkg.InterfaceView = None

        self.client = js_bridge.HivemindJSClient()
        self.scripts().insert(self.client)

        self.loadFinished.connect(self.bind_client, type=Qt.QueuedConnection)

    def load_view(self, view: interface_pkg.InterfaceView):
        self.view = view
        self.load(QtCore.QUrl('file://' + view.get_page()))

    def bind_client(self, ok: bool):
        key = self.client.key

        @threaded
        def bridge_thread():
            try:
                bridge_client = js_bridge.HivemindBridgeClient()
            except errors.HivemindError as e:
                app.display_error(e)
                return
            bridge_client.bind_send(js_bridge.claim_connection(key, bridge_client.on_recv))

        bridge_thread()

        new_client = js_bridge.HivemindJSClient()
        self.scripts().remove(self.client)
        self.scripts().insert(new_client)
        self.client = new_client

    def javaScriptConsoleMessage(
            self,
            level: QtWebEngineWidgets.QWebEnginePage.JavaScriptConsoleMessageLevel,
            message: str,
            line_number: int,
            source_id: str,
    ):
        print(message)

    def acceptNavigationRequest(
            self,
            url: QtCore.QUrl,
            type_: QtWebEngineWidgets.QWebEnginePage.NavigationType,
            is_main_frame: bool
    ) -> bool:
        if url.scheme() != 'file':
            return super().acceptNavigationRequest(url, type_, is_main_frame)
        if not url.path().startswith(self.view.root):
            url.setPath(self.view.root + url.path())
            self.setUrl(url)
        return super().acceptNavigationRequest(url, type_, is_main_frame)


class InterfaceManagePopup(XDialog):
    apply_btn: QtWidgets.QPushButton
    okay_btn: QtWidgets.QPushButton
    cancel_btn: QtWidgets.QPushButton
    table: QtWidgets.QTableWidget

    def __init__(self):
        super().__init__()
        self.load_xml('InterfaceManagePopup.xml')
        self.model = InterfaceSelectorModel.get_instance()
        self.model.available_interfaces_updated.connect(self.populate, type=Qt.QueuedConnection)
        self.model.update_available()

        self.apply_btn.mousePressEvent = self.apply_btn_push
        self.okay_btn.mousePressEvent = self.okay_btn_push
        self.cancel_btn.mousePressEvent = self.cancel_btn_push

    def populate(self):
        self.table.setRowCount(0)
        for package_name, interface_name in self.model.available_interfaces:
            row = self.table.rowCount()
            self.table.setRowCount(row + 1)
            
            for_pkg_box = QtWidgets.QTableWidgetItem()
            for_pkg_box.setText(package_name)
            for_pkg_box.setFlags(Qt.ItemIsSelectable)
            self.table.setItem(row, 0, for_pkg_box)

            interface_box = QtWidgets.QTableWidgetItem()
            interface_box.setText(interface_name)
            interface_box.setFlags(Qt.ItemIsSelectable)
            self.table.setItem(row, 1, interface_box)
            
            check_box = QtWidgets.QTableWidgetItem()
            if self.model.is_installed(interface_name):
                check_box.setCheckState(Qt.Checked)
            else:
                check_box.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 2, check_box)

    def apply_btn_push(self, event: QtCore.QEvent):
        self.accepted.emit()
        self.apply_changes()

    def okay_btn_push(self, event: QtCore.QEvent):
        self.accepted.emit()
        self.apply_changes()
        self.close()

    def cancel_btn_push(self, event: QtCore.QEvent):
        self.rejected.emit()
        self.close()
        
    def apply_changes(self):
        n_rows = self.table.rowCount()
        to_add = []
        to_remove = []
        for row_idx in range(n_rows):
            interface_name = self.table.item(row_idx, 1).text()
            checked = (self.table.item(row_idx, 2).checkState() == Qt.Checked)
            if checked and not self.model.is_installed(interface_name):
                to_add.append(interface_name)
            elif not checked and self.model.is_installed(interface_name):
                to_remove.append(interface_name)

        self.model.modify_interfaces(to_add, to_remove)


@register_xml('InterfacePage')
class InterfacePage(HBox):
    selector: QtWidgets.QTreeWidget
    display: QtWebEngineWidgets.QWebEngineView
    sync_btn: QtWidgets.QPushButton
    manage_btn: QtWidgets.QPushButton

    def __init__(self):
        super().__init__()
        self.load_xml('InterfacePage.xml')

        self.interface_model = InterfaceSelectorModel.get_instance()
        self.interface_model.interfaces_updated.connect(self.populate, type=Qt.QueuedConnection)
        self.interface_model.refresh()

        self.selector.header().hide()
        self.selector.itemActivated.connect(self.activated, type=Qt.QueuedConnection)

        self.page = InterfaceWebPage(self.display)
        self.display.setPage(self.page)

        self.sync_btn.mousePressEvent = self.sync_btn_press
        self.manage_btn.mousePressEvent = self.manage_btn_press
        
        self.dialog = InterfaceManagePopup()

    def populate(self):
        self.selector.clear()
        for name, interface in self.interface_model.interfaces.items():
            tl = QtWidgets.QTreeWidgetItem()
            tl.setText(0, name)
            tl.setExpanded(True)
            self.selector.addTopLevelItem(tl)
            for view in interface.views:
                vitem = InterfaceViewEntry(view)
                tl.addChild(vitem)
        self.selector.expandAll()

    def sync_btn_press(self, event: QtCore.QEvent):
        #self.interface_model.synchronize()
        app.display_error('multiline\nerror message\nvery\nmany\nlines!')

    def manage_btn_press(self, event: QtCore.QEvent):
        self.dialog.show()

    def activated(self, item: QtWidgets.QTreeWidgetItem, column: int):
        if not isinstance(item, InterfaceViewEntry):
            return
        self.page.load_view(item.view)


@register_xml('InterfaceNavButton')
class InterfaceNavButton(NavButton):
    text = 'interface'
    panel_class = InterfacePage
