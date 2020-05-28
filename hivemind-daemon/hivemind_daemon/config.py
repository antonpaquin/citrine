import os
from typing import *
import yaml


# TODO: windows path
config_root = os.path.join(os.getenv('HOME'), '.config', 'hivemind')


default_config = {
    'serve': {
        'host': '127.0.0.1',
        'port': 5402,
    },
    'storage_path': os.path.join(os.getenv('HOME'), '.cache', 'hivemind'),
    'worker_threads': 16,
}

# Possible feature: disable debug information in error responses
# Possible feature: enable / disable package changes
# Probable feature: specify repo URL

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
    config_fname = os.path.join(config_root, 'daemon.yaml')

    if os.path.isfile(config_fname):
        with open(config_fname, 'r') as in_f:
            user_config = yaml.safe_load(in_f)
    else:
        user_config = {}

    daemon_config = recursive_merge(base_config, user_config)

    if not os.path.isdir(config_root):
        os.makedirs(config_root)

    if not os.path.exists(config_fname):
        with open(config_fname, 'w') as out_f:
            yaml.dump(daemon_config, out_f)
        
        
def get_config(key: str):
    keys = key.split('.')
    c = daemon_config
    for k in keys:
        c = c[k]
    return c
