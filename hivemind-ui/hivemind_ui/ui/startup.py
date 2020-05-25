from hivemind_ui.qt_util import NavButton, VBox, register_xml


@register_xml('StartupPage')
class StartupPage(VBox):
    def __init__(self):
        super(StartupPage, self).__init__()
        self.load_xml('StartupPage.xml')
        self.show()


@register_xml('StartupNavButton')
class StartupNavButton(NavButton):
    text = 'startup'
    panel_class = StartupPage
