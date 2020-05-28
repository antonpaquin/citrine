import json
import queue
from typing import *

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtCore
import hivemind_client

from hivemind_ui import app, errors
from hivemind_ui.qt_util import HBox


def init_errors():
    ErrorSpawner.get_instance()


class ErrorSpawner(QtCore.QObject):
    """
    Utility to let random threads create error messages from anywhere
    """
    _instance: 'ErrorSpawner' = None
    
    sig_make_error: QtCore.SignalInstance = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.sig_make_error.connect(self._make_error, type=Qt.QueuedConnection)
        self.err_queue = queue.Queue()

    @staticmethod
    def get_instance() -> 'ErrorSpawner':
        # Make sure this is called on the main thread somewhere, 
        # ideally before it can be called from a thread somewhere else
        # (QT places objects on the thread they're created from)
        if ErrorSpawner._instance is None:
            ErrorSpawner._instance = ErrorSpawner()
        return ErrorSpawner._instance

    def send_error(self, message: Union[str, hivemind_client.errors.HivemindClientError, Dict]):
        self.err_queue.put(message)
        self.sig_make_error.emit()

    def _make_error(self):
        root = app.get_root()
        while not self.err_queue.empty():
            err = ErrorMessage(self.err_queue.get())
            err.setParent(root)
            err.show()


class ErrorMessage(HBox):
    message_label: QtWidgets.QLabel

    # TODO: expand error message
    # if the user clicks on the error, open up a dialog that doesn't auto-close with a copy-pastable error message

    def __init__(self, message: Union[str, hivemind_client.errors.HivemindClientError, Dict]):
        super().__init__()
        self.load_xml('ErrorBox.xml')
        
        if isinstance(message, hivemind_client.errors.HivemindClientError):
            self.message = json.dumps(message.to_dict(), indent=4)
        elif isinstance(message, errors.HivemindUiError):
            self.message = f'{message.name}: {message.message}'
        elif isinstance(message, dict):
            self.message = json.dumps(message, indent=4)
        else:
            self.message = str(message)

        self.message_label.setText(self.message)
        self.calculate_position()
        
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close, type=Qt.QueuedConnection)
        self.timer.start(5000)

    def calculate_position(self):
        lines = self.message.split('\n')
        margin = 50
        padding = 50
        self.message_label.setMargin(padding)
        fm = self.message_label.fontMetrics()
        x_size = max(fm.width(line) for line in lines) + (2 * padding)
        y_size = fm.lineSpacing() * len(lines) + (2 * padding)
        self.setFixedSize(x_size, y_size)
        root = app.get_root()
        xpos = root.size().width() - x_size - margin
        ypos = root.size().height() - y_size - margin
        #self.setStyleSheet("background-color: #00f")
        self.move(QtCore.QPoint(xpos, ypos))

    def close(self):
        self.hide()
