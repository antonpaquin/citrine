import logging

from hivemind_daemon import storage, server, package, logs, config


logger = logging.getLogger(__name__)


def main():
    config.init_config()
    storage.init_storage()
    logs.init_logging()
    logger.info('Hivemind v0.2.0')
    package.db.init_db()
    package.load.init_packages()
    server.parallel.init_workers(n_workers=config.get_config('worker_threads'))
    server.run_server(config.get_config('serve.host'), config.get_config('serve.port'))
