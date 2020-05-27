import gc
from typing import *

from PySide2.QtCore import Qt
from PySide2 import QtWidgets, QtCore
import hivemind_client

from hivemind_ui.ui.error import ErrorSpawner
from hivemind_ui.qt_util import HBox, VBox, register_xml


@register_xml('MainWrapper')
class MainWrapper(HBox):
    active_panel: QtWidgets.QFrame
    
    def __init__(self):
        super().__init__()
        self.load_xml('MainWrapper.xml')
        self.show()

        self.debug_frame_state = 0
        self.t = QtCore.QTimer()
        self.t.setInterval(50)
        self.t.setSingleShot(False)
        self.t.timeout.connect(self.debug_toggle_frames, type=Qt.QueuedConnection)
        self.t.start()
        
    def debug_toggle_frames(self):
        if self.debug_frame_state == 0:
            self.debug_frame_state = 1
            self.nav_panel.startup_button.mousePressEvent(None)
        else:
            self.debug_frame_state = 0
            self.nav_panel.package_button.mousePressEvent(None)

    def set_panel(self, panel: ClassVar[QtWidgets.QWidget]):
        if isinstance(self.active_panel, panel):
            return
        new_panel = panel()
        self.replaceWidget(self.active_panel, new_panel)
        #self.active_panel.destroy()
        self.active_panel = new_panel
        
    @staticmethod
    def display_error(message: Union[str, hivemind_client.errors.HivemindClientError, Dict]):
        ErrorSpawner.get_instance().send_error(message)


@register_xml('NavPanel')
class NavPanel(VBox):
    def __init__(self):
        super().__init__()
        self.load_xml('NavPanel.xml')
        self.show()
