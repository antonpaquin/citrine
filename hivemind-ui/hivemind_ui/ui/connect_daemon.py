import subprocess
import threading
from typing import Callable

from PySide2 import QtWidgets, QtGui
import hivemind_client

from hivemind_ui.qt_util import NavButton, HBox, qt_xml
import hivemind_ui.config as config


@qt_xml.register('ServerStatus')
class ServerStatus(QtWidgets.QLabel): pass


@qt_xml.register('ConnectionPage')
class ConnectionPage(HBox):
    host_box: QtWidgets.QLineEdit
    port_box: QtWidgets.QLineEdit
    spawn_daemon_btn: QtWidgets.QPushButton
    connect_btn: QtWidgets.QPushButton
    connect_status: QtWidgets.QLabel
    
    def __init__(self):
        super().__init__()
        self.load_xml('ConnectionPage.xml')

        self.port_box.setValidator(QtGui.QIntValidator())
        self.spawn_daemon_btn.mousePressEvent = self.spawn_daemon
        self.connect_btn.mousePressEvent = self.connect_server
        self.show()

    def connect_server(self: 'ConnectionPage', _: QtGui.QMouseEvent):
        def test_connection_thread():
            client = hivemind_client.api.HivemindClient(host=self.host_box.text(), port=int(self.port_box.text()))
            self.connect_status.setText('connecting...')
            try:
                client.heartbeat()
                self.connect_status.setText('connected')
                config.set_config('daemon.host', client.server.host)
                config.set_config('daemon.port', client.server.port)
            except hivemind_client.errors.ConnectionRefused as e:
                self.connect_status.setText(f'No server at specified location')
            except hivemind_client.errors.HivemindClientError as e:
                self.connect_status.setText(f'Failed: {e.name}')

        t = threading.Thread(target=test_connection_thread, daemon=True)
        t.start()

    def spawn_daemon(self, _: QtGui.QMouseEvent):
        subprocess.Popen(['hivemind-daemon'])


@qt_xml.register('ConnectionNavButton')
class ConnectionNavButton(NavButton):
    text = 'connection'
    panel_class = ConnectionPage
