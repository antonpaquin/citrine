import inspect  # don't worry it's fine
import json
import sys
from typing import Dict, Optional

from progress.bar import IncrementalBar

from hivemind_client import errors


def get_server():
    # TODO un-hardcode the connection info
    return '127.0.0.1', 5402


def subcommand_registry():
    handlers = {}
    # yo dawg I heard you like functions
    
    def subcommand_handler(command_name, err_stream=sys.stdout):
        def annotator(f):
            argspec = inspect.getfullargspec(f)  # functools wrap didn't do the job
            if 'parser' in argspec.args:
                def wrapped(args, parser):
                    try:
                        return f(args, parser=parser)
                    except errors.HivemindClientError as e:
                        print(f'{e.name}: {e.msg}', file=sys.stderr)
                        if e.data:
                            print(json.dumps(e.data, indent=4), file=err_stream)
            else:
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
    
    def dispatch(parser, args, key):
        if key not in args or args[key] is None:
            parser.print_help()
        else:
            handler = handlers[args[key]]
            argspec = inspect.getfullargspec(handler)
            if 'parser' in argspec.args:
                handler(args, parser=parser)
            else:
                handler(args)

    return subcommand_handler, dispatch


def make_progress_bar(label: str):
    bar: Optional[IncrementalBar] = None
    bar_progress = 0

    def fill_bar(data: Dict) -> None:
        nonlocal bar, bar_progress
        if not 'download-progress' in data and 'download-size' in data:
            return
        bar = bar or IncrementalBar(label, max=100, suffix='%(percent)d%%')

        percent = int(100 * data['download-progress'] / data['download-size'])
        while bar_progress < percent:
            bar.next()
            bar_progress += 1

    def finish_bar() -> None:
        if bar is not None:
            bar.finish()

    return fill_bar, finish_bar



    


