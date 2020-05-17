from json import JSONEncoder
from typing import Any, Callable

import numpy as np


class HivemindEncoder(JSONEncoder):
    encoder_registry = []

    def default(self, o: Any) -> Any:
        for cls, fn in HivemindEncoder.encoder_registry:
            if isinstance(o, cls):
                return fn(o)
        return f'Unserializable type <{type(o).__name__}>'

    @staticmethod
    def register_encoder(cls: Any, fn: Callable[[Any], Any]) -> None:
        HivemindEncoder.encoder_registry.append((cls, fn))


HivemindEncoder.register_encoder(np.ndarray, lambda x: x.tolist())
