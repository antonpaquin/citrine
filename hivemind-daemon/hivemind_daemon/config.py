import os
import platform
from typing import *
import warnings
import yaml


_platform = platform.system()
if _platform == 'Linux':
    storage_path = os.path.join(os.getenv('HOME'), '.cache', 'hivemind')
    config_path = os.path.join(os.getenv('HOME'), '.config', 'hivemind')
elif _platform == 'Windows':
    storage_path = os.path.join(os.getenv('APPDATA'), 'hivemind')
    config_path = os.path.join(os.getenv('APPDATA'), 'hivemind')
elif _platform == 'Darwin':
    storage_path = os.path.join(os.getenv('HOME'), '.cache', 'hivemind')
    config_path = os.path.join(os.getenv('HOME'), '.config', 'hivemind')
else:
    warnings.warn(f'Unknown platform {_platform}; defaulting storage to working directory')
    storage_path = os.getcwd()
    config_path = os.getcwd()


default_config = {
    'serve': {
        'host': '127.0.0.1',
        'port': 5402,
    },
    'storage_path': storage_path,
    'worker_threads': 16,
    'repository_url': 'https://raw.githubusercontent.com/antonpaquin/hivemind-repo/master/daemon/index',
}

# Possible feature: disable debug information in error responses
# Possible feature: enable / disable package changes

daemon_config = None  # type: Dict


def recursive_merge(base: Union[Dict, List, str, int], merge: Union[Dict, List, str, int]):
    if merge is None and base is not None:
        return base
    if base is None and merge is not None:
        return merge

    if isinstance(base, dict):
        keyset = set.union(set(base.keys()), set(merge.keys()))
        res = {}
        for k in keyset:
            res[k] = recursive_merge(base.get(k, None), merge.get(k, None))
        return res
            
    elif isinstance(base, list):
        return merge
    
    else:
        return merge
            

def init_config():
    global daemon_config

    base_config = default_config
    config_fname = os.path.join(config_path, 'daemon.yaml')

    if os.path.isfile(config_fname):
        with open(config_fname, 'r') as in_f:
            user_config = yaml.safe_load(in_f)
    else:
        user_config = {}

    daemon_config = recursive_merge(base_config, user_config)

    if not os.path.isdir(config_path):
        os.makedirs(config_path)

    if not os.path.exists(config_fname):
        with open(config_fname, 'w') as out_f:
            yaml.dump(daemon_config, out_f)
        
        
def get_config(key: str):
    keys = key.split('.')
    c = daemon_config
    for k in keys:
        c = c[k]
    return c
