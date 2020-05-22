from typing import *

from PySide2 import QtWidgets, QtWebEngineWidgets, QtCore

import hivemind_ui.app as app
from hivemind_ui.qt_util import VBox, NavButton, qt_xml


class InterfaceSelectorModel(QtCore.QObject):
    _instance: 'InterfaceSelectorModel' = None

    def __init__(self):
        super().__init__(parent=app.get_root())

        self.interfaces = {}  # type: Dict[str, List[str]]

    @staticmethod
    def getinstance() -> 'InterfaceSelectorModel':
        if InterfaceSelectorModel._instance is None:
            InterfaceSelectorModel._instance = InterfaceSelectorModel()
        return InterfaceSelectorModel._instance



@qt_xml.register('InterfacePage')
class InterfacePage(VBox):
    selector: QtWidgets.QTreeWidget
    display: QtWebEngineWidgets.QWebEngineView

    def __init__(self):
        super().__init__()
        self.load_xml('InterfacePage.xml')


@qt_xml.register('InterfaceNavButton')
class InterfaceNavButton(NavButton):
    text = 'interface'
    panel_class = InterfacePage
