import logging

from hivemind_daemon import storage, server, package, logs, config


logger = logging.getLogger(__name__)


def main():
    config.init_config()
    logs.init_logging()
    logger.info('Hivemind v0.1.0')
    storage.init_storage()
    package.db.init_db()
    package.load.init_packages()
    server.parallel.init_workers(n_workers=config.get_config('worker_threads'))
    server.run_server(config.get_config('serve.host'), config.get_config('serve.port'))
