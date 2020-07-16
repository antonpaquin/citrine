import logging
import time
from typing import Dict

import numpy as np
import onnxruntime

from citrine_daemon import errors
from citrine_daemon.util import truncate_str


logger = logging.getLogger(__name__)


class OnnxSession:
    sessions: Dict[str, 'OnnxSession'] = {}
    ttl = 30

    def __init__(self, model_file: str):
        self.model_file = model_file
        self.sess: onnxruntime.InferenceSession = None
        self.expire_timer = None
        self.reset_expiration()

    @staticmethod
    def get_session(model_file: str):
        if model_file not in OnnxSession.sessions:
            sess = OnnxSession.sessions[model_file]
            sess.reset_expiration()
        else:
            sess = OnnxSession(model_file)
            OnnxSession.sessions[model_file] = sess
        return sess
        
    def reset_expiration(self):
        self.expire_timer = time.time()

    @staticmethod
    def cleanup():
        t_now = time.time()
        for k, sess in OnnxSession.sessions.items():
            if (t_now - sess.expire_timer) > OnnxSession.ttl:
                OnnxSession.sessions.pop(k)
                
    def test_expire(self):
        if (self.expire_timer - time.time()) >= OnnxSession.ttl:
            OnnxSession.sessions.pop(self.model_file)
        

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
    logger.debug(f'Starting ONNX session for {model_file}', {'model': model_file})
    session = _get_session(model_file)
    inputs = coerce_types(raw_inputs, session)
    outputs = [n.name for n in session.get_outputs()]
    try:
        logger.debug('Running neural network')
        arr_out = session.run(outputs, inputs)
        logger.debug('Neural network inference complete')
    except onnxruntime.capi.onnxruntime_pybind11_state.InvalidArgument as e:
        raise errors.ModelRunError('Failed to run model', data=str(e))
    return {
        k: v
        for k, v in zip(outputs, arr_out)
    }

