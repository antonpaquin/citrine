import os
from typing import Any, Dict

from hivemind_ui import errors

default_config = {
    'daemon.server': '127.0.0.1',
    'daemon.port': 5402,
    'interface.inspector_port': 5404,
    'interface.scale_factor': 2,
    'js_bridge.socket.port': 5403,
    'storage.rootpath': os.path.join(os.getenv('HOME'), '.cache', 'hivemind', 'ui')
}


config_types = {
    'daemon.server': str,
    'daemon.port': int,
    'interface.inspector_port': int,
    'interface.scale_factor': int,
    'js_bridge.socket.port': int,
    'storage.rootpath': str,
}


def load_config() -> Dict[str, Any]:
    # TODO load config if it exists
    return default_config


def set_config(k: str, v: Any):
    Config.set(k, v)
    

def get_config(k: str) -> Any:
    return Config.get(k)


def items():
    return Config.items()


def typed_items(): 
    return [(k, config_types[k], v) for k, v in Config.items()]


class Config:
    _items: Dict[str, Any] = load_config()

    @staticmethod
    def set(k: str, v: Any):
        if k not in config_types:
            raise errors.ConfigError(f'Unknown config value {k}')
        t = config_types[k]
        try:
            Config._items[k] = t(v)
        except ValueError as e:
            raise errors.ConfigError(f'Value {v} is not valid for type {t.__name__}')

    @staticmethod
    def get(k: str) -> Any:
        return Config._items.get(k)

    @staticmethod
    def items():
        return Config._items.items()
    
    
class Transient:
    # For non-persistent config that is always reset at launch (aka program global state)
    _items: Dict[str, Any] = {}
    
    @staticmethod
    def set(k: str, v: Any):
        Transient._items[k] = v

    @staticmethod
    def get(k: str) -> Any:
        return Transient._items.get(k)

