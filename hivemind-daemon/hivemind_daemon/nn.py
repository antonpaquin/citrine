from typing import Dict

import numpy as np
import onnxruntime

from hivemind_daemon import storage, errors
from hivemind_daemon.util import truncate_str


def _get_session(model_file: str) -> onnxruntime.InferenceSession:
    session = onnxruntime.InferenceSession(model_file)
    return session


def assert_like_input(inputs: Dict) -> None:
    for k, v in inputs.items():
        if not isinstance(k, str):
            raise errors.InvalidInput(f'Key {truncate_str(k, 100)} does not look like the name of a model input')
        if not isinstance(v, np.ndarray):
            raise errors.InvalidTensor(
                'Value {value} for key {key} should be an numpy ndarray. Instead, got {vtype}'.format(
                    value=truncate_str(v, 100),
                    key=truncate_str(k, 100),
                    vtype=truncate_str(type(v), 100),
                )
            )
        
        
def coerce_types(raw_inputs: Dict[str, np.ndarray], session: onnxruntime.InferenceSession) -> Dict[str, np.ndarray]:
    """
    onnxruntime rejects, e.g., a float64 array passed as an input for a float32 tensor
    (annoying)
    Attempt to guess what it wants here and coerce, but default to no coercion if we don't know exactly
    """
    onnx_to_np = {
        'tensor(float)': np.float32,
    }
    res = {}
    for tensor_input in session.get_inputs():
        name = tensor_input.name
        try:
            if tensor_input.type in onnx_to_np:
                dtype = onnx_to_np[tensor_input.type]
                res[name] = raw_inputs[name].astype(dtype)
            else:
                res[name] = raw_inputs[name]
        except NameError:
            raise errors.InvalidInput(f'Could not find tensor {name} in input')
        except TypeError:
            raise errors.InvalidTensor(f'Could not coerce input {name} to type {tensor_input.type}')
    return res


def run_model(
        model_file: str,
        raw_inputs: Dict[str, np.ndarray],
) -> Dict[str, np.ndarray]:
    # TODO: session caching, batching
    # Probably once I have a garbage collector
    # I want to hold sessions in an LRU-like cache
    # (or have it be very configurable)
    # With possibly eviction weighted by memory size of the sessions
    session = _get_session(model_file)
    inputs = coerce_types(raw_inputs, session)
    outputs = [n.name for n in session.get_outputs()]
    try:
        arr_out = session.run(outputs, inputs)
    except onnxruntime.capi.onnxruntime_pybind11_state.InvalidArgument as e:
        raise errors.ModelRunError('Failed to run model', data=str(e))
    return {
        k: v
        for k, v in zip(outputs, arr_out)
    }

