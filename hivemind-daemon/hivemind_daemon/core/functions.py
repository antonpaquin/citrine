import logging
from typing import *

import cerberus
import numpy as np

from hivemind_daemon import errors, package

from .validator import HivemindValidator


logger = logging.getLogger(__name__)

NP_ARGT = Dict[str, np.ndarray]


function_lookup = {}  # type: Dict[int, Dict[str, Function]]


class Function(object):
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


def create_function(
        name: str,
        process_input: Callable[[Dict], Union[NP_ARGT, Tuple[NP_ARGT, Any]]],
        process_output: Union[Callable[[NP_ARGT], Dict], Callable[[NP_ARGT, Any], Dict]],
        model: str = None,
        input_validator: Dict = None,
) -> None:
    logger.info(f'Creating function {name}', {'function': name})
    # TODO: validate create function
    # This is basically the last staging area before whatever's in the wrapper becomes part of the API
    # Not that there needs to be more validation here,
    # but there can be

    if model is None:
        model = name

    if input_validator is not None:
        try:
            HivemindValidator(schema=input_validator)
        except cerberus.schema.SchemaError as e:
            raise errors.PackageInstallError('Package input_validator is incorrect', data=e.args[0])

    pkg = package.load.get_loading_package()  # type: package.DBPackage

    function = Function(
        name=name,
        package_id=pkg.rowid,
        model=model,
        process_input=process_input,
        process_output=process_output,
        input_validator=input_validator,
    )

    # package is always active or in the process of activating when this is called
    if pkg.rowid not in function_lookup:
        function_lookup[pkg.rowid] = {}
    if name not in function_lookup[pkg.rowid]:
        function_lookup[pkg.rowid][name] = function

    logger.info(f'Function {name} created for package id {pkg.rowid}', {'function': name, 'package_id': pkg.rowid})


def get_active_function(package_name: str, function_name: str) -> 'Function':
    pkg = package.DBPackage.from_name_latest(package_name, only_active=True)
    if pkg.rowid not in function_lookup:
        raise errors.MissingFunction(f'No active package {package_name}', 400)

    package_functions = function_lookup[pkg.rowid]
    if function_name not in package_functions:
        raise errors.MissingFunction(f'Package {package_name} has no function {function_name}', 400)

    return package_functions[function_name]


def list_active_function_names(package_id: int) -> List[str]:
    if package_id not in function_lookup:
        return []
    res = []
    for name, function in function_lookup[package_id].items():
        res.append(function.name)
    return res


def clear_functions(package_id: int):
    if package_id not in function_lookup:
        return
    function_lookup.pop(package_id)
