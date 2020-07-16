import base64
from typing import *

import numpy as np


def encode_tensor(arr: np.ndarray) -> Dict:
    data = base64.b64encode(arr)
    return {
        'dtype': str(arr.dtype),
        'data': data.decode('utf-8'),
        'shape': list(arr.shape),
    }


def decode_tensor(t: Dict) -> np.ndarray:
    arr = np.frombuffer(base64.b64decode(t['data']), t['dtype'])
    return arr.reshape(t['shape'])
