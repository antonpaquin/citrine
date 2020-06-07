import json
import sys

from hivemind_client import api, errors

import hivemind_client.cli.util as util
import hivemind_client.cli.package as package
import hivemind_client.cli.cli_io as cli_io


subcommand_handler, dispatch = util.subcommand_registry()
server, port = util.get_server()


@subcommand_handler('status')
def command_status(args):
    client = api.HivemindClient(server, port)
    status = client.heartbeat()
    print(json.dumps(status, indent=4))


@subcommand_handler('run')
def command_run(args):
    target = args['target']
    if args['in'] and args['in_json']:
        raise errors.OptionParseError('Cannot combine json input with -in')
    if args['in_json']:
        try:
            in_params = json.loads(args['in_json'])
        except json.JSONDecodeError:
            raise errors.OptionParseError('Positional input should be json. Are you missing a "-in" flag?')
    else:
        in_params = cli_io.parse_cli_inputs(args['in'] or [])
    out_params = cli_io.parse_cli_outputs(args['out'] or [])

    client = api.HivemindClient(server, port)
    results = client.run(target=target, params=in_params)

    if not out_params:
        print(json.dumps(results, indent=4))
    else:
        # cli_io has another hardcoded client in run_output
        cli_io.run_output(results, out_params)


@subcommand_handler('_run')
def command_run_raw(args):
    target_package = args['target_package']
    target_model = args['target_model']
    if args['in'] and args['in_json']:
        raise errors.OptionParseError('Cannot combine json input with -in')
    if args['in_json']:
        try:
            in_params = json.loads(args['in_json'])
        except json.JSONDecodeError:
            raise errors.OptionParseError('Positional input should be json. Are you missing a "-in" flag?')
    else:
        in_params = cli_io.parse_cli_inputs(args['in'] or [])
    out_params = cli_io.parse_cli_outputs(args['out'] or [])

    client = api.HivemindClient(server, port)
    results = client._run(target_package=target_package, target_model=target_model, params=in_params)

    if not out_params:
        print(json.dumps(results, indent=4))
    else:
        cli_io.run_output(results, out_params)


@subcommand_handler('result', err_stream=sys.stderr)
def command_result(args):
    client = api.HivemindClient(server, port)
    result = client.result(args['hash'])
    sys.stdout.buffer.write(result)


@subcommand_handler('install')
def command_install(args, parser):
    # Alias for "package install"
    package.dispatch(parser, args, 'command')


@subcommand_handler('package')
def command_package(args, parser):
    package.dispatch(parser, args, 'package_command')
