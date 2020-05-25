from typing import *

from PySide2 import QtWidgets, QtCore
from PySide2 import QtWebEngineWidgets

from hivemind_ui import app, interface_pkg, js_bridge
from hivemind_ui.qt_util import HBox, NavButton, register_xml
from hivemind_ui.util import threaded


class InterfaceSelectorModel(QtCore.QObject):
    _instance: 'InterfaceSelectorModel' = None

    interfaces_updated: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self):
        super().__init__(parent=app.get_root())

        self.interfaces = {}  # type: Dict[str, interface_pkg.Interface]

    @staticmethod
    def get_instance() -> 'InterfaceSelectorModel':
        if InterfaceSelectorModel._instance is None:
            InterfaceSelectorModel._instance = InterfaceSelectorModel()
        return InterfaceSelectorModel._instance

    @threaded
    def synchronize(self):
        interface_pkg.synchronize()
        self._refresh()

    @threaded
    def refresh(self):
        self._refresh()

    def _refresh(self):
        interfaces = interface_pkg.list_interfaces()
        self.interfaces = {interface.name: interface for interface in interfaces}
        self.interfaces_updated.emit()


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

        self.loadFinished.connect(self.bind_client)

    def load_view(self, view: interface_pkg.InterfaceView):
        self.view = view
        self.load(QtCore.QUrl('file://' + view.get_page()))

    def bind_client(self, ok: bool):
        key = self.client.key

        @threaded
        def bridge_thread():
            bridge_client = js_bridge.HivemindBridgeClient()
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
        self.interface_model.interfaces_updated.connect(self.populate)
        self.interface_model.refresh()

        self.selector.header().hide()
        self.selector.itemActivated.connect(self.activated)

        self.page = InterfaceWebPage(self.display)
        self.display.setPage(self.page)

        self.sync_btn.mousePressEvent = self.sync_btn_press

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
        self.interface_model.synchronize()

    def activated(self, item: QtWidgets.QTreeWidgetItem, column: int):
        if not isinstance(item, InterfaceViewEntry):
            return
        self.page.load_view(item.view)


@register_xml('InterfaceNavButton')
class InterfaceNavButton(NavButton):
    text = 'interface'
    panel_class = InterfacePage
