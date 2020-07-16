import base64
from typing import *

import numpy as np

from citrine_daemon import errors


def truncate_str(obj: Any, maxlength: int) -> str:
    # assume maxlength >= 3
    s = None
    try:
        s = str(obj)
    except errors.CitrineException:
        raise
    except Exception:
        try:
            s = repr(obj)
        except errors.CitrineException:
            raise
        except Exception:
            s = f'Unrepresentable object @{id(s)}'
            
    if len(s) > maxlength:
        s = s[:maxlength - 3] + '...'
    
    return s


def encode_tensor(arr: np.ndarray) -> Dict:
    if not arr.flags.c_contiguous:
        arr = arr.copy(order='C')
    data = base64.b64encode(arr)
    return {
        'dtype': str(arr.dtype),
        'data': data.decode('utf-8'),
        'shape': list(arr.shape),
    }


def decode_tensor(t: Dict) -> np.ndarray:
    arr = np.frombuffer(base64.b64decode(t['data']), t['dtype'])
    return arr.reshape(t['shape'])
