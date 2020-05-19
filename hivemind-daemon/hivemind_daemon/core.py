from typing import Dict, Callable, List

import cerberus
import numpy as np

from hivemind_daemon import errors, nn, package, storage


endpoint_lookup = {}  # type: Dict[str, List[Endpoint]]


def call(name: str, inputs: Dict = None) -> Dict:
    endpoint = get_active_endpoint(name)
    if endpoint.input_validator:
        v = cerberus.Validator(schema=endpoint.input_validator)
        if not v.validate(inputs):
            raise errors.ValidationError(v.errors)
        inputs = v.document
        
    try:
        model_inputs = endpoint.process_input(inputs)
    except errors.HivemindException:
        raise
    except Exception as e:
        raise errors.PackageError(f'Error in processing inputs for model {name}: {e}')

    nn.assert_like_input(model_inputs)
    db_model = package.db.DBModel.from_id_name(endpoint.package_id, endpoint.model)
    model_outputs = nn.run_model(storage.get_model_file(db_model), model_inputs)
    
    try:
        outputs = endpoint.process_output(model_outputs)
    except errors.HivemindException:
        raise
    except Exception as e:
        raise errors.PackageError(f'Error in processing outputs for model {name}: {e}')
    
    return outputs


def call_raw(package_name: str, model_name: str, inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    nn.assert_like_input(inputs)
    # TODO call_raw violates rules
    # It's actually very broken in this state
    # from_names isn't guaranteed unique
    # and this isn't making an 'active' check anywhere
    # might be able to get away with it by guaranteeing that only one package with a given name can be active at a time
    # In sql I can do that with a new table, but it's messier than what we have now
    # (create table ActivePackage (package_id rowid, package_name unique str))

    # Note that 'active' is mostly for constraining 'module.py', and `call_raw` can sidestep that by just sending numpy
    # directly. So is it OK to ignore here?
    db_model = package.db.DBModel.from_names(package_name, model_name)
    model_file = storage.get_model_file(db_model)
    return nn.run_model(model_file, inputs)


class Endpoint(object):
    def __init__(
            self,
            name: str,
            model: str,
            process_input: Callable[[Dict], Dict[str, np.ndarray]],
            process_output: Callable[[Dict[str, np.ndarray]], Dict],
            input_validator: Dict = None,
    ):
        self.name = name
        self.model = model
        self.process_input = process_input
        self.process_output = process_output
        self.input_validator = input_validator

        self.package_id = package.load.get_loading_package_id()  # type: int


def create_endpoint(
        name: str,
        process_input: Callable[[Dict], Dict[str, np.ndarray]],
        process_output: Callable[[Dict[str, np.ndarray]], Dict],
        model: str = None,
        input_validator: Dict = None,
) -> None:
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

    if name not in endpoint_lookup:
        endpoint_lookup[name] = []
        
    endpoint_lookup[name].append(Endpoint(
        name=name,
        model=model,
        process_input=process_input,
        process_output=process_output,
        input_validator=input_validator,
    ))


def get_active_endpoint(name: str) -> 'Endpoint':
    if name not in endpoint_lookup:
        raise errors.MissingEndpoint(f'No active candidate for endpoint {name}', 400)
    for candidate in endpoint_lookup[name]:
        db_package = package.db.DBPackage.from_id(candidate.package_id)  # from_id refreshes
        if db_package.active:
            return candidate
    raise errors.MissingEndpoint(f'All candidates for endpoint {name} are disabled', 400)
