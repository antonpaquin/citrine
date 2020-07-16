import json
import re
from typing import List, Dict, Tuple

import numpy as np
from PIL import Image

import citrine_client.errors as errors
import citrine_client.api as api
from citrine_client.util import encode_tensor


def parse_kv(kv_args: List[str]) -> List[Tuple[str, str]]:
    res = []
    for line in kv_args:
        if '=' not in line:
            raise errors.OptionParseError(f'Could not parse option "{line}"')
        radix = line.find('=')
        k = line[:radix]
        v = line[radix + 1:]
        res.append((k, v))
    return res


_renest_parse_rg = re.compile('((^|\.)[a-zA-Z]+[a-zA-Z0-9]?|\[[0-9]+\])')
_renest_parse_rg_full = re.compile('((^|\.)[a-zA-Z]+[a-zA-Z0-9]?|\[[0-9]+\])+')


def _parse_key(k: str) -> List[str]:
    if not _renest_parse_rg_full.fullmatch(k):
        raise errors.OptionParseError(f'Could not parse key {k}')
    groups = _renest_parse_rg.findall(k)
    res = []
    for group, _ in groups:
        if group.startswith('.'):
            res.append(group[1:])
        elif group.startswith('['):
            res.append(int(group[1:-1]))
        else:
            res.append(group)
    return res


def _transform_lists(d):
    if not isinstance(d, Dict):
        return _parse_value(d)
    if len(d) == 0:
        return {}
    keys = d.keys()
    # if it's a continuous 0-n integer sequence
    if all([isinstance(k, int) for k in keys]) and sorted(keys) == list(range(max(keys) + 1)):
        return [_transform_lists(d[k]) for k in range(max(keys) + 1)]
    else:
        return {
            k: _transform_lists(v)
            for k, v in d.items()
        }


def _parse_value(val: str):
    try:
        return int(val)
    except ValueError:
        pass

    try:
        return float(val)
    except ValueError:
        pass

    if val.startswith('@np:'):
        fname = val[len('@np:'):]
        try:
            load_arr = np.load(fname)
            # Do I have to worry about turning the ndarray into a python array?
            return encode_tensor(load_arr['arr_0'])  # default numpy save name
        except Exception as e:
            raise errors.OptionParseError(f'Could not parse numpy file {fname}')

    elif val.startswith('@img:'):
        fname = val[len('@img:'):]
        try:
            img = Image.open(fname)
            return encode_tensor(np.asarray(img))
        except Exception as e:
            raise errors.OptionParseError(f'Could not parse image file {fname}')

    elif val.startswith('@json:'):
        fname = val[len('@json:'):]
        try:
            with open(fname, 'r') as in_f:
                contents = in_f.read()
            return json.loads(contents)
        except Exception as e:
            raise errors.OptionParseError(f'Could not parse json file {fname}')

    elif val.startswith('@'):
        fname = val[len('@'):]
        try:
            with open(fname, 'r') as in_f:
                contents = in_f.read()
            return contents
        except Exception as e:
            raise errors.OptionParseError(f'Could not read file {fname}')

    return val


def run_output(results, output_kv):
    for key, key_str, command in output_kv:
        val = results
        try:
            for idx in key:
                val = val[idx]
        except Exception:
            raise errors.OptionParseError(f'Did not find {key_str} in the results')
        
        if isinstance(val, dict) and list(val.keys()) == ['file_ref']:
            # TODO undo hardcoding
            # FIX THIS
            client = api.CitrineClient('127.0.0.1', 5402)
            val = client.result(val['file_ref'])
            
        if command == 'print':
            if isinstance(val, dict) or isinstance(val, list):
                print(json.dumps(val, indent=4))
            else:
                print(val)
        else:
            fname = command
            if isinstance(val, bytes):
                mode = 'wb'
            else:
                mode = 'w'
            with open(fname, mode) as out_f:
                out_f.write(val)
            

def parse_cli_outputs(opts: List[str]):
    return [(_parse_key(k), k, v) for k, v in parse_kv(opts)]


def parse_cli_inputs(opts: List[str]) -> Dict:
    """
    1.
        For command line it's useful if some things come in with a "flat" format
        e.g.
            a[0].b=1 a[1].b=2 a[2].c=4 a[2].d=6
        should translate to
        {
            "a": [
                {"b": 1},
                {"b": 2},
                {"c": 4, "d": 6}
            ]
        }
    2.
        Numbers and numerics are autocoerced to int if possible, else float, else string
    3.
        Values starting with '@' are interpreted as files to be loaded with a special tool
        Parsers:
            @json:  -->  json
            @np:    -->  numpy array
            @img:   -->  numpy array (HWC)
            @       -->  file, read as text
    """
    flat = dict(parse_kv(opts))
    res = {}
    for k, v in flat.items():
        loc = res
        kx = _parse_key(k)
        for idx, token in enumerate(kx):
            if idx == len(kx)-1:
                loc[token] = v
            else:
                if token not in loc:
                    loc[token] = {}
                loc = loc[token]
    return _transform_lists(res)
