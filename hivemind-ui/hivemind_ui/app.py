from typing import *

from PySide2.QtWidgets import QApplication, QWidget
import hivemind_client

from hivemind_ui import ui, util, interface_pkg, js_bridge, qt_util


_root = None  # type: Optional[ui.MainWrapper]


def build_window() -> QWidget:
    global _root
    _root = ui.MainWrapper()
    _root.set_panel(ui.startup.StartupPage)
    _root.show()
    return _root


def get_root() -> ui.MainWrapper:
    return _root


def get_stylesheet():
    with open(util.get_resource('hivemind.css'), 'r') as in_f:
        style = in_f.read()
    return style


def init():
    interface_pkg.init_interfaces()
    util.init_threadpool()
    #js_bridge.init_server()
    qt_util.init_safeqobject()
    ui.error.init_errors()

    
def display_error(message: Union[str, hivemind_client.errors.HivemindClientError, Dict]):
    _root.display_error(message)


import faulthandler
faulthandler.enable()


def main():
    app = QApplication([])
    app.setStyleSheet(get_stylesheet())
    init()
    # If you don't init the main window and exec the app in the same context, the whole thing freezes / refuses to start
    # I think it's doing some kind of frame introspection in exec_ to figure out how to assign things to the app
    # Super annoying, but if this is still here I haven't figured out how to get around it
    w = build_window()
    import threading
    exit_code = app.exec_()
    print('Cleaning up...')
    exit(exit_code)
