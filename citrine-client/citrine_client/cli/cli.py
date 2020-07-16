import argparse

import citrine_client.cli.commands as commands


def package_subparser(parser: argparse.ArgumentParser):
    command = parser.add_subparsers(dest='package_command')

    install = command.add_parser('install')
    install.add_argument('name', nargs='*')
    install.add_argument('--specfile', nargs='+')
    install.add_argument('--localfile')
    install.add_argument('--url')
    install.add_argument('--hash')

    fetch = command.add_parser('fetch')
    fetch.add_argument('name', nargs='*')
    fetch.add_argument('--specfile', nargs='+')
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
    
    search = command.add_parser('search')
    search.add_argument('query')


def cli_args(parser: argparse.ArgumentParser):
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

    install_alias = command.add_parser('install')
    install_alias.add_argument('name', nargs='*')
    install_alias.add_argument('--specfile', nargs='+')
    install_alias.add_argument('--localfile')
    install_alias.add_argument('--url')
    install_alias.add_argument('--hash')


def main():
    parser = argparse.ArgumentParser()
    cli_args(parser)
    args = parser.parse_args().__dict__
    commands.dispatch(parser, args, 'command')
