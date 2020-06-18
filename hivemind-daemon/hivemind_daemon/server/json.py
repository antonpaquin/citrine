from json import JSONEncoder
import logging
from typing import Any, Callable

import numpy as np

from hivemind_daemon.util import encode_tensor


logger = logging.getLogger(__name__)


class HivemindEncoder(JSONEncoder):
    encoder_registry = []

    def default(self, o: Any) -> Any:
        for cls, fn in HivemindEncoder.encoder_registry:
            if isinstance(o, cls):
                return fn(o)
        type_name = type(o).__name__
        logger.warning(f'Tried to serialize unfamiliar type {type_name}', {'type_name': type_name})
        return f'Unserializable type <{type_name}>'

    @staticmethod
    def register_encoder(cls: Any, fn: Callable[[Any], Any]) -> None:
        HivemindEncoder.encoder_registry.append((cls, fn))


HivemindEncoder.register_encoder(np.ndarray, encode_tensor)
HivemindEncoder.register_encoder(np.float32, float)
HivemindEncoder.register_encoder(np.uint32, int)
HivemindEncoder.register_encoder(np.int32, int)
HivemindEncoder.register_encoder(np.uint8, int)
HivemindEncoder.register_encoder(np.int8, int)
