import platform
import subprocess

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtGui, QtCore
import citrine_client

from citrine_ui import app, config
from citrine_ui.qt_util import NavButton, HBox, register_xml
from citrine_ui.util import threaded


class DaemonConnection(QtCore.QObject):
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

        client = citrine_client.api.CitrineClient(host=server, port=port)
        try:
            self.state = DaemonConnection.TRY_CONNECT
            client.heartbeat()
            self.server = server
            self.port = port
            self.state = DaemonConnection.CONNECTED
            self.sig_connect_done.emit()
        except citrine_client.errors.ConnectionRefused as e:
            self.state = DaemonConnection.NO_CONNECTION
            app.display_error(e)
            self.sig_connect_error.emit(f'Connection refused')
        except citrine_client.errors.CitrineClientError as e:
            self.state = DaemonConnection.NO_CONNECTION
            app.display_error(e)
            self.sig_connect_error.emit(f'Failed: {e.name}')

    def spawn_daemon(self):
        _platform = platform.system()
        if _platform == 'Linux':
            subprocess.Popen(['citrine-daemon'])
        elif _platform == 'Windows':
            subprocess.Popen(['./citrine-daemon'])
        elif _platform == 'Darwin':
            subprocess.Popen(['./citrine-daemon'])
        else:
            subprocess.Popen(['citrine-daemon'])


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
