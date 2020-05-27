import hivemind_client


class HivemindUiError(Exception):
    name = 'UI Error'

    def __init__(self, client_msg: str):
        self.message = client_msg
        
        
class ConfigError(HivemindUiError): name = 'Config Error'
class UnknownConfigError(ConfigError):
    """
    User tried to set a config value that doesn't exist
    """
    name = 'Unknown Config'
        
class DownloadError(HivemindUiError): 
    name = 'Download Error'


class InterfaceError(HivemindUiError):
    """
    Interface == UI side package that's fetched from the web
    This is probably a mistake on the packager's part (3rd party)
    """
    name = 'Interface Error'


class TransportKeyError(HivemindUiError):
    """
    Nasty class of bug arising in the JS bridge 
    
    Happens if something in JS tries to connect to the same socket path twice, 
    or if something in UI tries to claim the same socket path twice,
    in very quick succession
    (immediately after we have one of each, the key is cleared)
    So functionally this probably means a race condition somewhere
    """
    name = 'Transport Error'


# Utility for multi-excepting
HivemindError = (HivemindUiError, hivemind_client.errors.HivemindClientError)
