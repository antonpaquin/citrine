from .main_wrap import MainWrapper

# These need to be imported _somewhere_ to trigger the xml registry
# Right now, that happens when 'app.py' imports the main wrapper
from . import startup, connect_daemon, edit_config, packages, interface, error
