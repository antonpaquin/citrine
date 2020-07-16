import json
import logging
from typing import *

from aiohttp import web

from citrine_daemon import errors
from citrine_daemon.server.json import CitrineEncoder
from citrine_daemon.server.parallel import AsyncFuture

logger = logging.getLogger(__name__)


def error_handler(f):
    async def wrapped(request):
        try:
            return await f(request)
        except errors.CitrineException as e:
            logger.info('Request failed', e.to_dict())
            return web.Response(
                body=json.dumps(e.to_dict()),
                status=e.status_code,
            )
        except Exception as e:
            logger.error('Request failed with unexpected error', errors.serialize_unknown_exception(e))
            raise
    return wrapped


def wrap_async(fn: Callable[[web.Request], Awaitable[AsyncFuture]]):
    async def wrapped(request: web.Request) -> web.Response:
        fut = await fn(request)
        return web.Response(
            body=json.dumps(fut, cls=CitrineEncoder),
            status=200
        )
    return wrapped


def wrap_sync(fn: Callable[[web.Request], Awaitable[AsyncFuture]]):
    async def wrapped(request: web.Request) -> web.Response:
        fut = await fn(request)
        result = await fut.result()
        if result is None:
            result = {'status': 'OK'}
        return web.Response(
            body=json.dumps(result, cls=CitrineEncoder),
            status=200,
        )
    return wrapped


# </weird abstract asynchronous craziness>
# In general, an endpoint for aiohttp server should be of type (web.Request -> web.Response)
# To facilitate keeping a synchronous and asynchronous version of the API, I instead have functions of type
# (web.Request -> AsyncFuture) which can be awaited via .result() or just returned on its own as a handle on a job in
# progress.
# wrap_sync and wrap_async handle converting those cases to web.Response properly


class AioServer:
    def __init__(self):
        self.routes = []
        self.async_routes = []
        self.submodules = []

    def add_submodule(self, prefix: str, submodule: 'AioServer'):
        self.submodules.append((prefix, submodule))
    
    def bind(self, app: web.Application, prefix: str = ''):
        routes = [
            web_method(f'{prefix}{path}', handler_fn)
            for web_method, path, handler_fn in self.routes
        ]
        app.add_routes(routes)
        async_routes = [
            web_method(f'/async{prefix}{path}', handler_fn)
            for web_method, path, handler_fn in self.async_routes
        ]
        app.add_routes(async_routes)
        for sub_prefix, submodule in self.submodules:
            submodule.bind(app, prefix=f'{prefix}{sub_prefix}')
            
    def route(self, method, path: str, fn, async_: bool = False, handle_errors: bool = True):
        assert method in [web.head, web.options, web.get, web.post, web.put, web.patch, web.delete, web.view]
        maybe_err_handler = error_handler if handle_errors else lambda x: x
        if async_:
            self.routes.append((method, path, maybe_err_handler(wrap_sync(fn))))
            self.async_routes.append((method, path, maybe_err_handler(wrap_async(fn))))
        else:
            self.routes.append((method, path, maybe_err_handler(fn)))
