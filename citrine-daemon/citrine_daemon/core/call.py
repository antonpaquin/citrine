import inspect
import logging
from typing import *

import numpy as np

from citrine_daemon import errors, package, storage
from . import nn, functions
from .validator import CitrineValidator


logger = logging.getLogger(__name__)

NP_ARGT = Dict[str, np.ndarray]


def call(package_name: str, function_name: str, inputs: Dict = None) -> Dict:
    logger.info(
        f'Attempting to call function {package_name}/{function_name}',
        {'package': package_name, 'function': function_name},
    )
    function = functions.get_active_function(package_name, function_name)
    if function.input_validator:
        v = CitrineValidator(schema=function.input_validator)
        if not v.validate(inputs):
            raise errors.ValidationError(v.errors)
        inputs = v.document

    try:
        logger.debug('Beginning 3rd party input processing')
        processed_input = function.process_input(inputs)
        logger.debug('Input processing completed')
    except errors.CitrineException:
        raise
    except Exception as e:
        logger.info('Input processing failed', {'error': e, 'args': e.args})
        raise errors.PackageError(f'Error in processing inputs for model {package_name}/{function_name}: {e}')
    
    if isinstance(processed_input, dict):
        model_input = processed_input
        ctx = None
        wants_ctx = False
    elif (
            isinstance(processed_input, tuple) 
            and len(processed_input) == 2 
            and isinstance(processed_input[0], dict)
    ):
        model_input, ctx = processed_input
        wants_ctx = True
    else:
        raise errors.PackageError('"process_input" format error. Acceptable return types are Dict or Tuple[Dict, Any]')

    nn.assert_like_input(model_input)
    db_model = package.db.DBModel.from_id_name(function.package_id, function.model)
    model_outputs = nn.run_model(storage.get_model_file(db_model), model_input)

    try:
        logger.debug('Beginning 3rd party output processing')
        if wants_ctx:
            outputs = function.process_output(model_outputs, ctx)
        else:
            outputs = function.process_output(model_outputs)
        logger.debug('Output processing completed')
    except errors.CitrineException:
        raise
    except Exception as e:
        logger.info('Output processing failed', {'error': e, 'args': e.args})
        raise errors.PackageError(f'Error in processing outputs for model {package_name}/{function_name}: {e}')

    return outputs


def call_raw(package_name: str, model_name: str, inputs: NP_ARGT) -> NP_ARGT:
    db_package = package.DBPackage.from_name_latest(package_name)
    db_model = package.DBModel.from_id_name(db_package.rowid, model_name)
    model_file = storage.get_model_file(db_model)
    return nn.run_model(model_file, inputs)


def output_wants_context(f: Callable) -> bool:
    signature = inspect.signature(f)
    if len(signature.parameters) > 1:
        return True
    for k, v in signature.parameters.items():
        if v.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    return False
