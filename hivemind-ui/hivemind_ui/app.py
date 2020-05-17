from typing import Optional

from PySide2.QtWidgets import QApplication, QWidget

from hivemind_ui.ui import MainWrapper, startup
from hivemind_ui.util import get_resource


_root = None  # type: Optional[MainWrapper]


def build_window() -> QWidget:
    global _root
    _root = MainWrapper()
    _root.set_panel(startup.StartupPage)
    _root.show()
    return _root


def get_root() -> MainWrapper:
    return _root


def get_stylesheet():
    with open(get_resource('hivemind.css'), 'r') as in_f:
        style = in_f.read()
    return style


def main():
    app = QApplication([])
    app.setStyleSheet(get_stylesheet())
    # If you don't init the main window and exec the app in the same context, the whole thing freezes / refuses to start
    # I think it's doing some kind of frame introspection in exec_ to figure out how to assign things to the app
    # Super annoying, but if this is still here I haven't figured out how to get around it
    w = build_window()
    exit(app.exec_())
