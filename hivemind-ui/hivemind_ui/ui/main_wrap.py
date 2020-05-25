from typing import ClassVar

from PySide2 import QtWidgets

from hivemind_ui.qt_util import HBox, VBox, register_xml


@register_xml('MainWrapper')
class MainWrapper(HBox):
    active_panel: QtWidgets.QFrame
    
    def __init__(self):
        super().__init__()
        self.load_xml('MainWrapper.xml')
        self.show()
        
    def set_panel(self, panel: ClassVar[QtWidgets.QWidget]):
        if isinstance(self.active_panel, panel):
            return
        new_panel = panel()
        self.replaceWidget(self.active_panel, new_panel)
        self.active_panel = new_panel


@register_xml('NavPanel')
class NavPanel(VBox):
    def __init__(self):
        super().__init__()
        self.load_xml('NavPanel.xml')
        self.show()
