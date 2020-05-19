import argparse

import hivemind_client.cli.commands as commands


def package_subparser(parser: argparse.ArgumentParser):
    command = parser.add_subparsers(dest='package_command')

    install = command.add_parser('install')
    install.add_argument('specfile', nargs='*')
    install.add_argument('--localfile')
    install.add_argument('--url')
    install.add_argument('--hash')

    fetch = command.add_parser('fetch')
    fetch.add_argument('specfile', nargs='*')
    fetch.add_argument('--localfile')
    fetch.add_argument('--url')
    fetch.add_argument('--hash')

    activate = command.add_parser('activate')
    activate.add_argument('name')
    activate.add_argument('--version')
    
    deactivate = command.add_parser('deactivate')
    deactivate.add_argument('name')
    deactivate.add_argument('--version')

    remove = command.add_parser('remove')
    remove.add_argument('name')
    remove.add_argument('--version')

    list_ = command.add_parser('list')


def cli_args(parser: argparse.ArgumentParser):
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
    
    command = parser.add_subparsers(dest='command', help='')
    
    package = command.add_parser('package')
    package_subparser(package)

    status = command.add_parser('status')
    
    run = command.add_parser('run')
    run.add_argument('target')
    run.add_argument('in_json', nargs='?')
    run.add_argument('-in', nargs='*')
    run.add_argument('-out', nargs='*')
    
    run_raw = command.add_parser('_run')
    run_raw.add_argument('target_package')
    run_raw.add_argument('target_model')
    run_raw.add_argument('in_json', nargs='?')
    run_raw.add_argument('-in', nargs='*')
    run_raw.add_argument('-out', nargs='*')
    
    result = command.add_parser('result')
    result.add_argument('hash')


def main():
    parser = argparse.ArgumentParser()
    cli_args(parser)
    args = parser.parse_args().__dict__
    commands.dispatch(parser, args, 'command')
