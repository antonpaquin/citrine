import json
import os
import platform
from typing import Any, Dict
import warnings

from hivemind_ui import errors


_platform = platform.system()
if _platform == 'Linux':
    storage_path = os.path.join(os.getenv('HOME'), '.cache', 'hivemind', 'ui')
    config_path = os.path.join(os.getenv('HOME'), '.config', 'hivemind-ui')
elif _platform == 'Windows':
    storage_path = os.path.join(os.getenv('APPDATA'), 'hivemind', 'ui')
    config_path = os.path.join(os.getenv('APPDATA'), 'hivemind', 'ui')
elif _platform == 'Darwin':
    storage_path = os.path.join(os.getenv('HOME'), '.cache', 'hivemind', 'ui')
    config_path = os.path.join(os.getenv('HOME'), '.config', 'hivemind-ui')
else:
    warnings.warn(f'Unknown platform {_platform}; defaulting storage to working directory')
    storage_path = os.getcwd()
    config_path = os.getcwd()


default_config = {
    'daemon.server': '127.0.0.1',
    'daemon.port': 5402,
    'interface.inspector_port': 5404,
    'interface.scale_factor': 1,
    'js_bridge.socket.port': 5403,
    'repo.index': 'https://raw.githubusercontent.com/antonpaquin/hivemind-repo/master/ui/index',
    'repo.package_index': 'https://raw.githubusercontent.com/antonpaquin/hivemind-repo/master/ui/package_interface',
    'storage.rootpath': storage_path,
    'ui.hidpi': False,
}


config_types = {
    'daemon.server': str,
    'daemon.port': int,
    'interface.inspector_port': int,
    'interface.scale_factor': int,
    'js_bridge.socket.port': int,
    'repo.index': str,
    'repo.package_index': str,
    'storage.rootpath': str,
    'ui.hidpi': bool,
}


def load_config() -> Dict[str, Any]:
    fname = os.path.join(config_path, 'hivemind-ui.json')
    if os.path.exists(fname):
        with open(fname, 'r') as in_f:
            res = json.load(in_f)
    else:
        res = default_config
    write_config(res)
    return res


def write_config(config):
    if not os.path.isdir(config_path):
        os.makedirs(config_path)
    fname = os.path.join(config_path, 'hivemind-ui.json')
    with open(fname, 'w') as out_f:
        json.dump(config, out_f, indent=4)


def set_config(k: str, v: Any):
    Config.set(k, v)
    

def get_config(k: str) -> Any:
    return Config.get(k)


def items():
    return Config.items()


def typed_items(): 
    return [(k, config_types[k], v) for k, v in Config.items()]


def _coerce_bool(x):
    if x in {'0', 'False', 'false'}:
        return False
    return True


class Config:
    _items: Dict[str, Any] = load_config()

    @staticmethod
    def set(k: str, v: Any):
        if k not in config_types:
            raise errors.ConfigError(f'Unknown config value {k}')
        t = config_types[k]
        if t == bool:
            t = _coerce_bool
        try:
            Config._items[k] = t(v)
        except ValueError as e:
            raise errors.ConfigError(f'Value {v} is not valid for type {t.__name__}')
        write_config(Config._items)

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

