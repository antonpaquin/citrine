import json
import os
from typing import *

import requests

from hivemind_client import errors


def package_install_params(
        name: str = None,
        specfile: str = None,
        localfile: str = None,
        url: str = None,
        package_hash: str = None,
) -> Dict:
    if name is not None:
        request_data = {'jsn': {'name': name}}
    elif specfile is not None:
        if not os.path.isfile(specfile):
            raise errors.FileNotFound(f'Could not find file {specfile}')
        with open(specfile, 'rb') as in_f:
            filedata = in_f.read()
        request_data = {'files': {'specfile': filedata}}
    elif localfile is not None:
        request_data = {'jsn': {'localfile': localfile}}
    elif url is not None and package_hash is not None:
        request_data = {'jsn': {'url': url, 'hash': package_hash}}
    else:
        raise errors.InvalidOptions(
            'You must specify "name" or one of "specfile", "localfile", ("url" + "package_hash")'
        )
    
    return request_data


def wrap_request(req, *args, **kwargs):
    r = None
    try:
        r = req(*args, **kwargs)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        raise errors.ServerError('Connection timed out')
    except requests.exceptions.HTTPError:
        raise errors.ServerError('Request failed', data={'response': r.content.decode('utf-8')})
    except requests.exceptions.ConnectionError:
        raise errors.ConnectionRefused('Failed to connect to server')
    
    return r.content

