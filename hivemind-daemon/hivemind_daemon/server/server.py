import json
import os
from typing import Callable, Awaitable, Dict

import aiofiles
from aiohttp import web
import cerberus
import numpy as np

import hivemind_daemon
from hivemind_daemon import errors, storage, package
from hivemind_daemon.server.json import HivemindEncoder
from hivemind_daemon.server.parallel import AsyncFuture, run_async, get_future


def error_handler(f):
    async def wrapped(request):
        try:
            return await f(request)
        except errors.HivemindException as e:
            return web.Response(
                body=json.dumps(e.to_dict()),
                status=e.status_code,
            )
    return wrapped


def wrap_async(fn: Callable[[web.Request], Awaitable[AsyncFuture]]):
    @error_handler
    async def wrapped(request: web.Request) -> web.Response:
        fut = await fn(request)
        return web.Response(
            body=json.dumps(fut, cls=HivemindEncoder),
            status=200
        )
    return wrapped


def wrap_sync(fn: Callable[[web.Request], Awaitable[AsyncFuture]]):
    @error_handler
    async def wrapped(request: web.Request) -> web.Response:
        fut = await fn(request)
        result = await fut.result()
        if result is None:
            result = {'status': 'OK'}
        return web.Response(
            body=json.dumps(result, cls=HivemindEncoder),
            status=200,
        )
    return wrapped


# </weird abstract asynchronous craziness>
# In general, an endpoint for aiohttp server should be of type (web.Request -> web.Response)
# To facilitate keeping a synchronous and asynchronous version of the API, instead all these functions are of type
# (web.Request -> AsyncFuture) which can be awaited via .result() or just returned on its own as a handle on a job in 
# progress.
# wrap_sync and wrap_async handle converting those cases to web.Response properly


async def get_formdata(request: web.Request) -> Dict:
    res = {}
    async for formdata in await request.multipart():
        res[formdata.name] = await formdata.text()
    return res


async def _package_install_spec(request: web.Request):
    if request.content_type == 'multipart/form-data':
        formdata = await get_formdata(request)
        if 'specfile' not in formdata:
            raise errors.InvalidInput('Missing specfile')
        try:
            jsn = json.loads(formdata['specfile'])
        except json.JSONDecodeError:
            raise errors.ValidationError('specfile was not valid json')
    else:
        try:
            jsn = await request.json()
        except json.JSONDecodeError:
            raise errors.ValidationError('Request was not json')
    if 'localfile' in jsn:
        validator = cerberus.Validator(schema={
            'localfile': {
                'type': 'string',
                'required': True,
            }
        })
    elif 'url' in jsn:
        validator = cerberus.Validator(schema={
            'url': {
                'type': 'string',
                'required': True,
            },
            'hash': {
                'type': 'string',
                'required': True,
            },
        })
    else:
        raise errors.ValidationError('You must provide one of "localfile" or "url"')
    if not validator.validate(jsn):
        raise errors.ValidationError('Request failed to validate', data=validator.errors)
    return validator.document


async def expect_json(request: web.Request, validator: cerberus.Validator) -> Dict:
    try:
        jsn = await request.json()
    except json.JSONDecodeError:
        raise errors.ValidationError('Request does not appear to be json')
    if not validator.validate(jsn):
        raise errors.ValidationError('Input failed to validate', data=validator.errors)
    return validator.document


# Start endpoint defs

async def run_network(request: web.Request) -> AsyncFuture:
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
    })


async def run_network_raw(request: web.Request) -> AsyncFuture:
    """
    low-level run exactly this network with exactly these inputs
    """
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
    })


async def package_fetch(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, but don't load / run any code
    """
    params = await _package_install_spec(request)
    if 'localfile' in params:
        return run_async(package.install.install_package_file, kwargs={
            'localfile': params['localfile'],
            'activate': False,
        })
    elif 'url' in params and 'hash' in params:
        return run_async(package.install.install_package_url, kwargs={
            'url': params['url'],
            'package_hash': params['hash'],
            'activate': False,
        })
    else:
        raise errors.InternalError('Invalid package spec made it through validation')


async def package_pull(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, then load the module and make it available
    """
    params = await _package_install_spec(request)
    if 'localfile' in params:
        return run_async(package.install.install_package_file, kwargs={
            'localfile': params['localfile'],
            'activate': True,
        })
    elif 'url' in params and 'hash' in params:
        return run_async(package.install.install_package_url, kwargs={
            'url': params['url'],
            'package_hash': params['hash'],
            'activate': True,
        })
    else:
        raise errors.InternalError('Invalid package spec made it through validation')


async def package_activate(request: web.Request) -> AsyncFuture:
    pass


async def package_deactivate(request: web.Request) -> AsyncFuture:
    pass


async def package_remove(request: web.Request) -> AsyncFuture:
    pass

    
async def daemon_install(request: web.Request) -> AsyncFuture:
    v = cerberus.Validator(schema={
        'type': {
            'type': 'string',
            'required': False,
            'default': 'url',
            'allowed': ['url', 'file'],
        },
        'link': {
            'type': 'string',
            'required': True,
        },
        'hash': {
            'type': 'string',
            'required': False,
            'default': '',
        }
    })
    params = await expect_json(request, v)
    if params['type'] == 'url' and not params['hash']:
        raise errors.ValidationError('Input failed to validate', data={'type': {'url': ['requires hash']}})

    return run_async(package.install.install_package, kwargs={
        'package_type': params['type'],
        'link': params['link'],
        'hash': params['hash'],
    })


async def install(request: web.Request) -> AsyncFuture:
    v = cerberus.Validator(schema={
        'url': {
            'type': 'string',
            'required': True,
        },
        'hash': {
            'type': 'string',
            'required': True,
        },
    })
    formdata = await get_formdata(request)
    if 'hivespec' not in formdata:
        raise errors.InvalidInput('Missing hivespec file')
    try:
        jsn = json.loads(formdata['hivespec'])
    except Exception:
        raise errors.InvalidInput(f'Hivespec file should be json formatted')
    if not v.validate(jsn):
        raise errors.ValidationError('Input failed to validate', data=v.errors)
    params = v.document

    return run_async(hivemind_daemon.package.install_package, kwargs={
        'package_type': 'url',
        'link': params['url'],
        'hash': params['hash'],
    })


async def heartbeat(request: web.Request) -> web.Response:
    return web.Response(body=json.dumps({
        'status': 'OK',
        'service': 'hivemind-daemon',
        'version': '0.0.1',
    }))


async def get_result(request: web.Request) -> web.Response:
    fpath = os.path.join(storage.results_path, request.match_info['name'])
    if not os.path.isfile(fpath):
        return web.Response(status=404)
    async with aiofiles.open(fpath, 'rb') as in_f:
        contents = await in_f.read()
    return web.Response(body=contents)


@error_handler
async def async_status(request: web.Request) -> web.Response:
    fut = get_future(request.match_info['uid'])
    return web.Response(
        body=json.dumps(fut, cls=HivemindEncoder),
        status=200
    )


@error_handler
async def async_cancel(request: web.Request) -> web.Response:
    fut = get_future(request.match_info['uid'])
    fut.interrupt()
    return web.Response(
        body=json.dumps(fut, cls=HivemindEncoder),
        status=200
    )


def build_app():
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
        (web.post, '/package/pull', package_pull),
        (web.post, '/package/activate', package_activate),
        (web.post, '/package/deactivate', package_deactivate),
        (web.post, '/package/remove', package_remove),
    ]
    
    for method, route, fn in asynchronizable:
        app.add_routes([
            method(route, wrap_sync(fn)),
            method('/async' + route, wrap_async(fn))
        ])

    return app


def run_server(host, port):
    web.run_app(
        app=build_app(),
        host=host,
        port=port,
    )
