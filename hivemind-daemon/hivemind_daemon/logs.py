import json
import logging
import os

from hivemind_daemon import package, server, storage


class HivemindFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        async_job = server.parallel.get_active_job()
        loading_package = package.load.get_loading_package()
        res = {
            'logger': record.name,
            'level': record.levelname,
            'message': record.msg,
            'data': record.args,
            'timestamp': record.created,
            'reltime': record.relativeCreated / 1000,
            'thread': record.threadName,
            'context': {
                'function': record.funcName,
                'line': record.lineno,
                'file': record.filename,
                'path': record.pathname,
                'module': record.module,
            },
            'program': 'hivemind-daemon',
            'loading_package': loading_package.rowid if loading_package else None,
            'async_job_id': async_job.uid if async_job else None,
            'request_info': async_job.request_info if async_job else None,
        }
            
        return json.dumps(res, cls=server.json.HivemindEncoder)
        

def init_logging():
    logging.logMultiprocessing = False
    logging.logProcesses = False

    log_fpath = os.path.join(storage.root_path(), 'hivemind.log')
    root_logger = logging.getLogger('')
    handler = logging.FileHandler(log_fpath)
    handler.setFormatter(HivemindFormatter())
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    
    aio_logger = logging.getLogger('aiohttp')
    aio_logger.setLevel(logging.WARNING)
