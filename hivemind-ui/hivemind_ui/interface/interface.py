import json
import os
import shutil
import tempfile
from typing import *
import zipfile

import cerberus
import hivemind_client

import hivemind_ui.config as config
import hivemind_ui.interface.download as download


"""

So I've got a bunch of packages on daemon that collectively imply a bunch of interfaces should be available on UI

How does the UI get them?

1. The UI downloads them

2. The daemon downloads them and then serves to the UI

1 is nice but tough to manage. 
2 breaks encapsulation -- the server should be able to operate without realizing that a UI even exists

Say we go 1.
    - How does the UI figure out what to download?
    - What does it do if the download fails?
    - How does it react to changes in the daemon's packages?
    - How does someone test locally?

If it fails: throw an error, eventually alert the user
How does it react to change in wanted interfaces: change the interfaces
How does someone test locally: manually stick the package in the proper directory and/or I can build an interface for it

How does it figure out what to download?
    - In the interfaces menu, stick two buttons: synchronize, manage
    - Synchronize just does it as automatically as I can manage: fetch all interfaces for given packages
        - In most cases 'all' will mean 0 or 1
    - Manage opens a dialog where we can see package -> interface relationship -- maybe a 2 column table?
    - Once it's displayed like that, it's viable to just hit the button and it installs or removes
    
How does synchronize know?
    - Somewhere on the web there's a package -> interface mapping: the index
    - Specify the index url via config
    - Try to download and cache it each time you synchronize

So a lot of this is starting to depend on web infrastructure -- these files are available at that website, etc
Seems to be a complete picture, without that, but I was hoping on sticking things in AWS _after_ all this was all done
and ready to demo

Strategy:
    - Ignore the "manage" bit for now, which includes removing interfaces
    - Stub out / mock network calls
        - Eventually: GET index --> GET interface
        - For now: index at file --> interface at file
        
The form of the interface in the index (package -> interface):
    - I can have (name) or (url, hash)
        package -> name -> (url, hash) -> zipfile:
            - name implies another index: name -> (url, hash) -> zipfile
            - Maybe this exists in the package repo?
            - kinda long of a chain
        package -> (url, hash) -> zipfile:
            - somewhat harder to update, maybe?
            - I need a name -> (url, hash) anyway -- `hivemind-ui install foo kinda thing`
                - Not that there's a cli, but that will drive the 'manage' part of things
"""


metadata_validator = {
    'name': {
        'type': 'string',
        'required': True,
    },
    'human_name': {
        'type': 'string',
        'required': False,
    },
    'views': {
        'type': 'dict',
        'keysrules': {
            'type': 'string',
        },
        'values': {
            'type': 'dict',
            'schema': {
                'root': {
                    'type': 'string',
                    'required': True,
                },
                'page': {
                    'type': 'string',
                    'required': True,
                },
            },
        },
    },
    'requires_daemon': {
        'type': 'list',
        'schema': {
            'type': 'string',
        },
    },
}


# TODO: invalidate old package->interface index
package_interface_index = None  
interface_index = None


def init_interfaces():
    interface_dir = os.path.join(config.get_config('storage.rootpath'), 'interfaces')
    if not os.path.isdir(interface_dir):
        os.makedirs(interface_dir)
    download_dir = os.path.join(config.get_config('storage.rootpath'), 'download')
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)
        
        
def synchronize():
    for interface in check_wanted_interfaces():
        url, hashsum = locate_interface(interface)
        if url.startswith('/'):
            fname = url
        else:
            fname = download.get_file(url, hashsum)
        install_from_zip(fname)


def install_from_zip(zip_fname: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_fname) as zip_f:
            for fname in zip_f.filelist:
                zip_f.extract(fname, tmpdir)
        install_from_temp(tmpdir)
        

def parse_metadata_file(fname: str):
    with open(fname, 'r') as in_f:
        meta = json.load(in_f)
    validator = cerberus.Validator(schema=metadata_validator)
    if not validator.validate(meta):
        raise RuntimeError(json.dumps(validator.errors))
    return validator.document


def install_from_temp(tmpdir: str):
    metadata_fname = os.path.join(tmpdir, 'meta.json')
    meta = parse_metadata_file(metadata_fname)
    interface_name = meta['name']
    interface_fpath = os.path.join(config.get_config('storage.rootpath'), 'interfaces', interface_name)
    if os.path.exists(interface_fpath):
        # TODO: handle interface collision
        shutil.rmtree(interface_fpath)
    os.makedirs(interface_fpath)

    for fname in os.listdir(tmpdir):
        shutil.copy(fname, interface_fpath)


def check_wanted_interfaces() -> List[str]:
    client = hivemind_client.HivemindClient(config.get_config('daemon.server'), config.get_config('daemon.port'))
    list_packages = [p['name'] for p in client.package.list()['packages']]
    pi_index = get_package_interface_index()
    wanted_interfaces = []
    for package in list_packages:
        if package in pi_index:
            wanted_interfaces.append(pi_index[package])
    return wanted_interfaces


def locate_interface(name: str) -> Tuple[str, str]:
    index = get_interface_index()
    return index[name]


def get_interface(url: str, file_hash: str):
    dl_file = download.get_file(url, file_hash)
    
    with tempfile.TemporaryDirectory() as tmpdir, zipfile.ZipFile(dl_file) as zip_f:
        for fname in zip_f.filelist:
            zip_f.extract(fname, tmpdir)
        install_from_temp(tmpdir)
        

def get_package_interface_index() -> Dict[str, str]:
    # TODO: package_interface_index on web
    # This is a stubbed out version that pulls from the local machine
    # Eventually this wants to 'requests' out to amazon or something
    global package_interface_index
    sep = '|'
    repo_root = '/home/anton/code/hivemind/mock-repo'

    if package_interface_index is None:
        fname = os.path.join(repo_root, 'ui', 'package_interface')
        with open(fname, 'r') as in_f:
            raw = in_f.readlines()

        package_interface_index = {}
        for line in raw:
            package, interface = line.strip().split(sep)
            package_interface_index[package] = interface

    return package_interface_index


def get_interface_index() -> Dict[str, Tuple[str, str]]:
    # TODO: interface_index on web
    # This is a stubbed out version that pulls from the local machine
    # Eventually this wants to 'requests' out to amazon or something
    global interface_index
    sep = '|'
    repo_root = '/home/anton/code/hivemind/mock-repo'

    if interface_index is None:
        fname = os.path.join(repo_root, 'ui', 'index')
        with open(fname, 'r') as in_f:
            raw = in_f.readlines()

        interface_index = {}
        for line in raw:
            name, url, hashsum = line.strip().split(sep)
            interface_index[name] = (url, hashsum)

    return interface_index
