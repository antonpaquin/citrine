import subprocess

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtGui, QtCore
import hivemind_client

from hivemind_ui import app, config
from hivemind_ui.qt_util import NavButton, HBox, register_xml, SafeQObject
from hivemind_ui.util import threaded


class DaemonConnection(SafeQObject):
    NO_CONNECTION = 0
    TRY_CONNECT = 1
    CONNECTED = 2

    _instance: 'DaemonConnection' = None

    sig_connect_done: QtCore.SignalInstance = QtCore.Signal()
    sig_connect_error: QtCore.SignalInstance = QtCore.Signal(str)

    def __init__(self, server: str, port: int):
        super().__init__(parent=app.get_root())
        self.state = DaemonConnection.NO_CONNECTION
        self.server = server
        self.port = port

    @staticmethod
    def get_instance() -> 'DaemonConnection':
        if DaemonConnection._instance is None:
            DaemonConnection._instance = DaemonConnection(
                server=config.get_config('daemon.server'),
                port=config.get_config('daemon.port'),
            )
        return DaemonConnection._instance

    @threaded
    def daemon_connect(self, server: str, port: int):
        self.state = DaemonConnection.NO_CONNECTION

        client = hivemind_client.api.HivemindClient(host=server, port=port)
        try:
            self.state = DaemonConnection.TRY_CONNECT
            client.heartbeat()
            self.server = server
            self.port = port
            self.state = DaemonConnection.CONNECTED
            self.sig_connect_done.emit()
        except hivemind_client.errors.ConnectionRefused as e:
            self.state = DaemonConnection.NO_CONNECTION
            app.display_error(e)
            self.sig_connect_error.emit(f'Connection refused')
        except hivemind_client.errors.HivemindClientError as e:
            self.state = DaemonConnection.NO_CONNECTION
            app.display_error(e)
            self.sig_connect_error.emit(f'Failed: {e.name}')

    def spawn_daemon(self):
        subprocess.Popen(['hivemind-daemon'])


@register_xml('ServerStatus')
class ServerStatus(QtWidgets.QLabel): pass


@register_xml('ConnectionPage')
class ConnectionPage(HBox):
    host_box: QtWidgets.QLineEdit
    port_box: QtWidgets.QLineEdit
    spawn_daemon_btn: QtWidgets.QPushButton
    connect_btn: QtWidgets.QPushButton
    connect_status: QtWidgets.QLabel

    def __init__(self):
        super().__init__()
        self.load_xml('ConnectionPage.xml')

        self.model = DaemonConnection.get_instance()
        self.model.sig_connect_done.connect(self.connection_finished, type=Qt.QueuedConnection)
        self.model.sig_connect_error.connect(self.connection_error, type=Qt.QueuedConnection)

        self.port_box.setValidator(QtGui.QIntValidator())
        self.spawn_daemon_btn.mousePressEvent = self.spawn_btn_press
        self.connect_btn.mousePressEvent = self.connect_btn_press

    def connect_btn_press(self: 'ConnectionPage', _: QtGui.QMouseEvent):
        self.model.daemon_connect(self.host_box.text(), int(self.port_box.text()))
        self.connect_status.setText('connecting...')

    def connection_finished(self):
        self.connect_status.setText('connected')

    def connection_error(self, err: str):
        self.connect_status.setText(err)

    def spawn_btn_press(self, _: QtGui.QMouseEvent):
        self.model.spawn_daemon()


@register_xml('ConnectionNavButton')
class ConnectionNavButton(NavButton):
    text = 'connection'
    panel_class = ConnectionPage
