from hivemind_ui.ui.main_wrap import MainWrapper

# These need to be imported _somewhere_ to trigger the xml registry
# Right now, that happens when 'app.py' imports the main wrapper
import hivemind_ui.ui.startup as startup
import hivemind_ui.ui.connect_daemon as connect_daemon
import hivemind_ui.ui.edit_config as edit_config
import hivemind_ui.ui.packages as packages
import hivemind_ui.ui.interface as interface
import hivemind_ui.ui.error as error
