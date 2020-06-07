import inspect
import logging
from typing import *

import cerberus
import numpy as np

from hivemind_daemon import errors, nn, package, storage


logger = logging.getLogger(__name__)

endpoint_lookup = {}  # type: Dict[str, List[Endpoint]]
package_endpoints = {}  # type: Dict[int, List[Endpoint]]

NP_ARGT = Dict[str, np.ndarray]


def call(name: str, inputs: Dict = None) -> Dict:
    logger.info(f'Attempting to call endpoint {name}', {'endpoint': name})
    endpoint = get_active_endpoint(name)
    if endpoint.input_validator:
        v = cerberus.Validator(schema=endpoint.input_validator)
        if not v.validate(inputs):
            raise errors.ValidationError(v.errors)
        inputs = v.document

    try:
        logger.debug('Beginning 3rd party input processing')
        processed_input = endpoint.process_input(inputs)
        logger.debug('Input processing completed')
    except errors.HivemindException:
        raise
    except Exception as e:
        logger.info('Input processing failed', {'error': e, 'args': e.args})
        raise errors.PackageError(f'Error in processing inputs for model {name}: {e}')
    
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
    db_model = package.db.DBModel.from_id_name(endpoint.package_id, endpoint.model)
    model_outputs = nn.run_model(storage.get_model_file(db_model), model_input)

    try:
        logger.debug('Beginning 3rd party output processing')
        if wants_ctx:
            outputs = endpoint.process_output(model_outputs, ctx)
        else:
            outputs = endpoint.process_output(model_outputs)
        logger.debug('Output processing completed')
    except errors.HivemindException:
        raise
    except Exception as e:
        logger.info('Output processing failed', {'error': e, 'args': e.args})
        raise errors.PackageError(f'Error in processing outputs for model {name}: {e}')

    return outputs


def call_raw(package_name: str, model_name: str, inputs: NP_ARGT) -> NP_ARGT:
    db_package = package.DBPackage.from_name_latest(package_name)
    db_model = package.DBModel.from_id_name(db_package.rowid, model_name)
    model_file = storage.get_model_file(db_model)
    return nn.run_model(model_file, inputs)


class Endpoint(object):
    def __init__(
            self,
            name: str,
            package_id: int,
            model: str,
            process_input: Callable[[Dict], Union[NP_ARGT, Tuple[NP_ARGT, Any]]],
            process_output: Union[Callable[[NP_ARGT], Dict], Callable[[NP_ARGT, Any], Dict]],
            input_validator: Dict = None,
    ):
        self.name = name
        self.package_id = package_id
        self.model = model
        self.process_input = process_input
        self.process_output = process_output
        self.input_validator = input_validator


def create_endpoint(
        name: str,
        process_input: Callable[[Dict], Union[NP_ARGT, Tuple[NP_ARGT, Any]]],
        process_output: Union[Callable[[NP_ARGT], Dict], Callable[[NP_ARGT, Any], Dict]],
        model: str = None,
        input_validator: Dict = None,
) -> None:
    logger.info(f'Creating endpoint {name}', {'endpoint': name})
    # TODO: validate create endpoint
    # This is basically the last staging area before whatever's in the wrapper becomes part of the API
    # Not that there needs to be more validation here,
    # but there can be

    if model is None:
        model = name

    if input_validator is not None:
        try:
            cerberus.Validator(schema=input_validator)
        except cerberus.schema.SchemaError as e:
            raise errors.PackageInstallError('Package input_validator is incorrect', data=e.args[0])

    package_id = package.load.get_loading_package_id()  # type: int

    endpoint = Endpoint(
        name=name,
        package_id=package_id,
        model=model,
        process_input=process_input,
        process_output=process_output,
        input_validator=input_validator,
    )

    if package_id not in package_endpoints:
        package_endpoints[package_id] = []
    package_endpoints[package_id].append(endpoint)

    if name not in endpoint_lookup:
        endpoint_lookup[name] = []
    endpoint_lookup[name].append(endpoint)

    logger.info(f'Endpoint {name} created for package id {package_id}', {'endpoint': name, 'package_id': package_id})


def get_active_endpoint(name: str) -> 'Endpoint':
    if name not in endpoint_lookup:
        raise errors.MissingEndpoint(f'No active candidate for endpoint {name}', 400)
    for candidate in endpoint_lookup[name]:
        db_package = package.db.DBPackage.from_id(candidate.package_id)  # from_id refreshes
        if db_package.active:
            return candidate
    raise errors.MissingEndpoint(f'All candidates for endpoint {name} are disabled', 400)


def list_active_endpoint_names(package_id: int) -> List[str]:
    if package_id not in package_endpoints:
        return []
    res = []
    for endpoint in package_endpoints[package_id]:
        res.append(endpoint.name)
    return res


def clear_endpoints(package_id: int):
    if package_id not in package_endpoints:
        return
    for remove_endpoint in package_endpoints[package_id]:
        name = remove_endpoint.name
        if name not in endpoint_lookup:
            break
        ii = 0
        while ii < len(endpoint_lookup[name]):
            if endpoint_lookup[name][ii] is remove_endpoint:
                endpoint_lookup[name].pop(ii)
            else:
                ii += 1
    package_endpoints.pop(package_id)
    
    
def output_wants_context(f: Callable) -> bool:
    signature = inspect.signature(f)
    if len(signature.parameters) > 1:
        return True
    for k, v in signature.parameters.items():
        if v.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    return False
