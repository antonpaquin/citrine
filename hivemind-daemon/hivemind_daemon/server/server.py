import json
import logging
import os

import aiofiles
from aiohttp import web
import cerberus
import numpy as np

import hivemind_daemon
from hivemind_daemon import errors, storage, package
from hivemind_daemon.server.json import HivemindEncoder
from hivemind_daemon.server.util import *
from hivemind_daemon.server.parallel import AsyncFuture, run_async, get_future


logger = logging.getLogger(__name__)


async def run_network(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method run')
    if not request.body_exists:
        jsn = {}
    else:
        try:
            jsn = await request.json()
        except json.decoder.JSONDecodeError as e:
            # TODO: support protobuf input
            raise errors.InvalidInput('Input should be JSON')

    # TODO run_network multipart inputs
    # I'll probably want to handle the case where the user uploads an image at some point, which means exposing that to
    # the intermediate loader at some point.
    # Already have a method for reading multipart, just need to decide on a function signature
    
    return run_async(hivemind_daemon.core.call, kwargs={
        'name': request.match_info['name'], 
        'inputs': jsn,
    }, request_info=make_request_info('run'))


async def run_network_raw(request: web.Request) -> AsyncFuture:
    """
    low-level run exactly this network with exactly these inputs
    """
    logger.debug('Handling request for method _run')
    if not request.body_exists:
        jsn = {}
    else:
        try:
            jsn = await request.json()
        except json.decoder.JSONDecodeError as e:
            # TODO: support protobuf input
            raise errors.InvalidInput('Input should be JSON')

    # I am not able to come up with an input which np.asarray will fail on
    # It juts coerces everything to object, which onnxruntime should be able to reject smoothly
    model_args = {str(k): np.asarray(v) for k, v in jsn.items()}
    
    return run_async(hivemind_daemon.core.call_raw, kwargs={
        'package_name': request.match_info['packagename'],
        'model_name': request.match_info['modelname'],
        'inputs': model_args,
    }, request_info=make_request_info('_run'))


async def package_fetch(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, but don't load / run any code
    """
    logger.debug('Handling request for method package.fetch')
    params = await package_install_spec(request)
    if 'localfile' in params:
        return run_async(package.install.install_package_file, kwargs={
            'localfile': params['localfile'],
            'activate': False,
        }, request_info=make_request_info('package.fetch'))
    elif 'url' in params and 'hash' in params:
        return run_async(package.install.install_package_url, kwargs={
            'url': params['url'],
            'package_hash': params['hash'],
            'activate': False,
        }, request_info=make_request_info('package.fetch'))
    else:
        raise errors.InternalError('Invalid package spec made it through validation')


async def package_install(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, then load the module and make it available
    """
    logger.debug('Handling request for method package.install')
    params = await package_install_spec(request)
    if 'localfile' in params:
        return run_async(package.install.install_package_file, kwargs={
            'localfile': params['localfile'],
            'activate': True,
        }, request_info=make_request_info('package.install'))
    elif 'url' in params and 'hash' in params:
        return run_async(package.install.install_package_url, kwargs={
            'url': params['url'],
            'package_hash': params['hash'],
            'activate': True,
        }, request_info=make_request_info('package.install'))
    else:
        raise errors.InternalError('Invalid package spec made it through validation')


async def package_activate(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method package.activate')
    validator = cerberus.Validator(schema={
        'name': {
            'type': 'string',
            'required': True,
        },
        'version': {
            'type': 'string',
            'required': False,
            'nullable': True,
            'default': None,
        },
    })
    params = await expect_json(request, validator)
    return run_async(package.load.activate_package, kwargs={
        'name': params['name'],
        'version': params['version'],
    }, request_info=make_request_info('package.activate'))


async def package_deactivate(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method package.deactivate')
    # Maybe I can come up with a way to join these two?
    # Just needs a good metaphor for the api
    validator = cerberus.Validator(schema={
        'name': {
            'type': 'string',
            'required': True,
        },
        'version': {
            'type': 'string',
            'required': False,
            'nullable': True,
            'default': None,
        },
    })
    params = await expect_json(request, validator)
    return run_async(package.load.deactivate_package, kwargs={
        'name': params['name'],
        'version': params['version'],
    }, request_info=make_request_info('package.deactivate'))


async def package_remove(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method package.remove')
    validator = cerberus.Validator(schema={
        'name': {
            'type': 'string',
            'required': True,
        },
        'version': {
            'type': 'string',
            'required': False,
            'nullable': True,
            'default': None,
        },
    })
    params = await expect_json(request, validator)
    return run_async(package.install.remove_package, kwargs={
        'name': params['name'],
        'version': params['version'],
    }, request_info=make_request_info('package.remove'))


async def package_list(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method package.list')
    return run_async(package.db.list_packages, request_info=make_request_info('package.list'))


async def heartbeat(request: web.Request) -> web.Response:
    logger.debug('Handling request for method heartbeat')
    return web.Response(body=json.dumps({
        'status': 'OK',
        'service': 'hivemind-daemon',
        'version': '0.0.1',
    }))


async def get_result(request: web.Request) -> web.Response:
    logger.debug('Handling request for method result')
    fpath = os.path.join(storage.results_path, request.match_info['name'])
    if not os.path.isfile(fpath):
        return web.Response(status=404)
    async with aiofiles.open(fpath, 'rb') as in_f:
        contents = await in_f.read()
    return web.Response(body=contents)


@error_handler
async def async_status(request: web.Request) -> web.Response:
    logger.debug('Handling request for method async.status')
    fut = get_future(request.match_info['uid'])
    return web.Response(
        body=json.dumps(fut, cls=HivemindEncoder),
        status=200
    )


@error_handler
async def async_cancel(request: web.Request) -> web.Response:
    logger.debug('Handling request for method async.cancel')
    fut = get_future(request.match_info['uid'])
    fut.interrupt()
    return web.Response(
        body=json.dumps(fut, cls=HivemindEncoder),
        status=200
    )


def build_app():
    logger.debug('Initializing async server')
    app = web.Application()

    app.add_routes([
        web.get('/', heartbeat),
        web.get('/result/{name}', get_result),
        web.get('/async/get/{uid}', async_status),
        web.get('/async/cancel/{uid}', async_cancel),
    ])
    
    asynchronizable = [
        (web.post, '/run/{name}', run_network),
        (web.post, '/_run/{packagename}/{modelname}', run_network_raw),

        (web.post, '/package/fetch', package_fetch),
        (web.post, '/package/install', package_install),
        (web.post, '/package/activate', package_activate),
        (web.post, '/package/deactivate', package_deactivate),
        (web.post, '/package/remove', package_remove),
        (web.get, '/package/list', package_list),
    ]
    
    for method, route, fn in asynchronizable:
        app.add_routes([
            method(route, wrap_sync(fn)),
            method('/async' + route, wrap_async(fn))
        ])

    logger.debug('Async server ready')
    return app


def run_server(host, port):
    logger.info(f'Running app at {host}:{port}', {'host': host, 'port': port})
    web.run_app(
        app=build_app(),
        host=host,
        port=port,
    )
