from collections import namedtuple
import queue
import threading
from typing import *

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import Qt

from hivemind_ui import errors


"""
I think creating QObjects in threads is causing random segfaults.
Solution is to make sure they're all created on the main thread,
but I _want_ to get objects in strange threads on occasion.

Hence this mess.
"""


def init_safeqobject():
    QObjectFactory.get_instance()


class SafeQObject(QtCore.QObject):
    def __init__(self, parent=None):
        if parent:
            super().__init__(parent=parent)
        else:
            super().__init__()
        if threading.current_thread().name != 'MainThread':
            raise errors.HivemindUiError('Tried to create QObject from non-main thread')

    @classmethod
    def init_safe(cls, *args, **kwargs):
        """
        Send cls and args to the factory to get instantiated on the main thread (via QT signals)
        Use a threading lock to block until the creation is complete,
        and return the results via a list (pretend it's a pointer)
        """
        if threading.current_thread().name == 'MainThread':
            return cls(*args, **kwargs)

        factory = QObjectFactory.get_instance()
        waitlock = threading.Lock()
        waitlock.acquire()
        ref = []
        factory.create(cls, args, kwargs, waitlock, ref)
        waitlock.acquire()
        return ref[0]
    

class QObjectFactory(SafeQObject):
    _instance = None
    sig_create: QtCore.SignalInstance = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.work_queue = queue.Queue()
        self.sig_create.connect(self._create, type=Qt.QueuedConnection)
        
    @staticmethod
    def get_instance():
        if QObjectFactory._instance is None:
            QObjectFactory._instance = QObjectFactory()
        return QObjectFactory._instance

    def create(self, cls, args, kwargs, waitlock, ref):
        self.work_queue.put((cls, args, kwargs, waitlock, ref))
        self.sig_create.emit()
        
    def _create(self):
        cls: ClassVar; args: Tuple; kwargs: Dict; waitlock: threading.Lock; ref: List
        while not self.work_queue.empty():
            cls, args, kwargs, waitlock, ref = self.work_queue.get()
            instance = cls(*args, **kwargs)
            ref.append(instance)
            waitlock.release()
            


