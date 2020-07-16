import gc
from typing import *

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtCore
import citrine_client

from citrine_ui.ui.error import ErrorSpawner
from citrine_ui.qt_util import HBox, VBox, register_xml


@register_xml('MainWrapper')
class MainWrapper(HBox):
    active_panel: QtWidgets.QFrame
    
    def __init__(self):
        super().__init__()
        self.load_xml('MainWrapper.xml')
        self.show()

        # Frequently creating and destroying panels seems to lead to segfaults
        # I think it's a GC / ref counting issue, but I'm not sure how to make sure everything is cleaned up
        # when QT wants it to be
        # So just give up and don't frequently create / destroy panels
        self.panels = {}
        
    def set_panel(self, panel: ClassVar[QtWidgets.QWidget]):
        if isinstance(self.active_panel, panel):
            return
        
        if panel.__name__ in self.panels:
            new_panel = self.panels[panel.__name__]
        else:
            new_panel = panel()
            self.panels[panel.__name__] = new_panel

        old_panel = self.active_panel
        self.active_panel = new_panel

        self.replaceWidget(old_panel, new_panel)
        old_panel.hide()
        new_panel.show()


    @staticmethod
    def display_error(message: Union[str, citrine_client.errors.CitrineClientError, Dict]):
        ErrorSpawner.get_instance().send_error(message)


@register_xml('NavPanel')
class NavPanel(VBox):
    def __init__(self):
        super().__init__()
        self.load_xml('NavPanel.xml')
        self.show()
