import logging

from aiohttp import web
from .api import get_server


logger = logging.getLogger(__name__)


def build_app():
    logger.debug('Initializing async server')
    app = web.Application()

    server = get_server()
    server.bind(app)

    # override default 1M -> 1G
    app._client_max_size = 1024 ** 3

    logger.debug('Async server ready')
    return app


def run_server(host, port):
    logger.info(f'Running app at {host}:{port}', {'host': host, 'port': port})
    web.run_app(
        app=build_app(),
        host=host,
        port=port,
    )
