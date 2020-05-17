from PySide2 import QtWidgets
from PySide2.QtCore import Qt

from hivemind_ui.qt_util import NavButton, VBox, qt_xml


@qt_xml.register('StartupPage')
class StartupPage(VBox):
    def __init__(self):
        super(StartupPage, self).__init__()
        self.load_xml('StartupPage.xml')
        self.show()


@qt_xml.register('StartupNavButton')
class StartupNavButton(NavButton):
    text = 'startup'
    panel_class = StartupPage
