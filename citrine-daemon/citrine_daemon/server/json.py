from json import JSONEncoder
import logging
from typing import Any, Callable

import numpy as np

from citrine_daemon.util import encode_tensor


logger = logging.getLogger(__name__)


class CitrineEncoder(JSONEncoder):
    encoder_registry = []

    def default(self, o: Any) -> Any:
        for cls, fn in CitrineEncoder.encoder_registry:
            if isinstance(o, cls):
                return fn(o)
        type_name = type(o).__name__
        logger.warning(f'Tried to serialize unfamiliar type {type_name}', {'type_name': type_name})
        return f'Unserializable type <{type_name}>'

    @staticmethod
    def register_encoder(cls: Any, fn: Callable[[Any], Any]) -> None:
        CitrineEncoder.encoder_registry.append((cls, fn))


CitrineEncoder.register_encoder(np.ndarray, encode_tensor)
CitrineEncoder.register_encoder(np.float32, float)
CitrineEncoder.register_encoder(np.uint32, int)
CitrineEncoder.register_encoder(np.int32, int)
CitrineEncoder.register_encoder(np.uint8, int)
CitrineEncoder.register_encoder(np.int8, int)
