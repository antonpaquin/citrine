import json
import logging
import os

import aiofiles
from aiohttp import web

from citrine_daemon import storage
from citrine_daemon.server.parallel import get_future
from citrine_daemon.server.json import CitrineEncoder

from .aio_server import AioServer


logger = logging.getLogger(__name__)


def get_base_server():
    server = AioServer()

    server.route(web.get, '/', heartbeat, handle_errors=False)
    server.route(web.get, '/result/{name}', get_result, handle_errors=False)
    server.route(web.get, '/async/get/{uid}', async_status)
    server.route(web.get, '/async/cancel/{uid}', async_cancel)
    
    return server


async def heartbeat(request: web.Request) -> web.Response:
    logger.debug('Handling request for method heartbeat')
    return web.Response(body=json.dumps({
        'status': 'OK',
        'service': 'citrine-daemon',
        'version': '0.3.0',
    }))


async def get_result(request: web.Request) -> web.Response:
    logger.debug('Handling request for method result')
    fpath = os.path.join(storage.results_path(), request.match_info['name'])
    if not os.path.isfile(fpath):
        return web.Response(status=404)
    async with aiofiles.open(fpath, 'rb') as in_f:
        contents = await in_f.read()
    return web.Response(body=contents)


async def async_status(request: web.Request) -> web.Response:
    logger.debug('Handling request for method async.status')
    fut = get_future(request.match_info['uid'])
    return web.Response(
        body=json.dumps(fut, cls=CitrineEncoder),
        status=200
    )


async def async_cancel(request: web.Request) -> web.Response:
    logger.debug('Handling request for method async.cancel')
    fut = get_future(request.match_info['uid'])
    fut.interrupt()
    return web.Response(
        body=json.dumps(fut, cls=CitrineEncoder),
        status=200
    )
