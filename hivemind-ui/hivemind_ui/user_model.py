import threading
from typing import *

from PySide2 import QtCore
import hivemind_client

from hivemind_ui.config import get_config


class DaemonPackage(object):
    def __init__(self, name: str, human_name: str, version: str, active: bool):
        self.name = name
        self.human_name = human_name
        self.version = version
        self.active = active
        

class PackageInProgress(object):
    def __init__(self, name: str):
        self.name = name
        self.value = 0
        self.maximum = 1
        
    def update(self, data: Dict):
        if 'download-progress' not in data or 'download-size' not in data:
            return
        self.value = data['download-progress']
        self.maximum = data['download-size']
