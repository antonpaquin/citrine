import logging

from hivemind_daemon import storage, server, package, logs


logger = logging.getLogger(__name__)


def main():
    logs.init_logging()
    logger.info('Hivemind v0.0.1')
    storage.init_storage()
    package.db.init_db()
    package.load.init_packages()
    server.parallel.init_workers(n_workers=16)
    server.run_server('127.0.0.1', 5402)
