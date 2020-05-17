import argparse
import json
import sys

import hivemind_client.api as api
import hivemind_client.errors as errors
import hivemind_client.util as util
import hivemind_client.cli_io as cli_io


handlers = {}


def subcommand_handler(command_name, err_stream=sys.stdout):
    def annotator(f):
        def wrapped(args):
            try:
                return f(args)
            except errors.HivemindClientError as e:
                print(f'{e.name}: {e.msg}', file=sys.stderr)
                if e.data:
                    print(json.dumps(e.data, indent=4), file=err_stream)
        handlers[command_name] = wrapped
        return wrapped
    return annotator
        

@subcommand_handler('install')
def command_install(args):
    res = []
    for fname in args['specfile']:
        fill_bar, finish_bar = util.make_progress_bar(f'Downloading package for {fname}: ')

        print(f'Installing {fname}')
        try:
            result = api.install(fname, progress_callback=fill_bar)
        finally:
            finish_bar()
        res.append(result)
    print(json.dumps(res, indent=4))
        

@subcommand_handler('daemon-install')
def command_daemon_install(args):
    params = dict(cli_io.parse_kv(args['params']))
    param_keys = set(params.keys())
    allowed_configurations = [
        {'file'},
        {'link', 'hash'},
    ]
    if not any([param_keys == c for c in allowed_configurations]):
        raise errors.OptionParseError(f'Invalid options', data={
            'allowed': [list(k) for k in allowed_configurations],
            'given': list(param_keys),
        })

    if 'file' in params:
        result = api.daemon_install(package_type='file', link=params['file'])
    elif 'link' in params and 'hash' in params:
        fill_bar, finish_bar = util.make_progress_bar(f'Downloading package from {params["link"]}: ')
        try:
            result = api.daemon_install(
                package_type='url',
                link=params['link'],
                package_hash=params['hash'],
                progress_callback=fill_bar,
            )
        finally:
            finish_bar()
    else:
        raise errors.OptionParseError('should never get here')

    print(json.dumps(result, indent=4))


@subcommand_handler('status')
def command_status(args):
    status = api.heartbeat()
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
    results = api.run(target=target, params=in_params)
    if not out_params:
        print(json.dumps(results, indent=4))
    else:
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
    results = api._run(target_package=target_package, target_model=target_model, params=in_params)
    if not out_params:
        print(json.dumps(results, indent=4))
    else:
        cli_io.run_output(results, out_params)


@subcommand_handler('result', err_stream=sys.stderr)
def command_result(args):
    result = api.result(args['hash'])
    sys.stdout.buffer.write(result)


def cli_args():
    """"""
    ' e.x.'
    'hivemind install foo.hivespec'
    'hivemind daemon-install link=foo hash=auto'
    'hivemind daemon-install file=/foo/bar/baz'  # alias for type=file
    'hivemind status'  # alias for heartbeat
    'hivemind run twdne3 @foo'  # load file as json, send it
    'hivemind run twdne3 a=@foo b.a=foo b.c=foo b.d.0=foo'  # build a dictionary with jq-like syntax
    'hivemind _run twdne3 a=@foo b=0.5 c=[[0.1]]'
    'hivemind result foohash'  # get-result

    'hivemind run TWDNEv3 truncation=0.7 -out images[0]=foo.png'
    
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', help='')
    
    parser_install = commands.add_parser('install')
    parser_install.add_argument('specfile', nargs='+')
    
    parser_dinstall = commands.add_parser('daemon-install')
    parser_dinstall.add_argument('params', nargs='*')
    
    parser_status = commands.add_parser('status')
    
    parser_run = commands.add_parser('run')
    parser_run.add_argument('target')
    parser_run.add_argument('in_json', nargs='?')
    parser_run.add_argument('-in', nargs='*')
    parser_run.add_argument('-out', nargs='*')
    
    parser_run_raw = commands.add_parser('_run')
    parser_run_raw.add_argument('target_package')
    parser_run_raw.add_argument('target_model')
    parser_run_raw.add_argument('in_json', nargs='?')
    parser_run_raw.add_argument('-in', nargs='*')
    parser_run_raw.add_argument('-out', nargs='*')
    
    parser_result = commands.add_parser('result')
    parser_result.add_argument('hash')

    args = parser.parse_args()
    return parser, args.__dict__


def main():
    parser, args = cli_args()
    if 'command' not in args or args['command'] is None:
        parser.print_help()
    else:
        handlers[args['command']](args)
