import json
import logging
import time
import traceback
from typing import *

from aiohttp import web
import cerberus

from citrine_daemon import errors, package
from citrine_daemon.server.json import CitrineEncoder
from citrine_daemon.server.parallel import AsyncFuture


__all__ = [
    'error_handler',
    'wrap_sync',
    'wrap_async',
    'get_formdata',
    'package_install_spec',
    'package_install_command',
    'expect_json',
    'make_request_info',
]

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
    @error_handler
    async def wrapped(request: web.Request) -> web.Response:
        fut = await fn(request)
        return web.Response(
            body=json.dumps(fut, cls=CitrineEncoder),
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
            body=json.dumps(result, cls=CitrineEncoder),
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


async def package_install_spec(request: web.Request):
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
    elif 'name' in jsn:
        validator = cerberus.Validator(schema={
            'name': {
                'type': 'string',
                'required': True,
            },
        })
    else:
        raise errors.ValidationError('You must provide one of "localfile", "url", "name"')
    if not validator.validate(jsn):
        raise errors.ValidationError('Request failed to validate', data=validator.errors)
    return validator.document


def package_install_command(params: Dict, activate: bool) -> Tuple[Optional[Callable], Optional[Dict]]:
    if 'localfile' in params:
        return package.install.install_package_file, {
            'localfile': params['localfile'],
            'activate': activate,
        }
    elif 'url' in params and 'hash' in params:
        return package.install.install_package_url, {
            'url': params['url'],
            'package_hash': params['hash'],
            'activate': activate,
        }
    elif 'name' in params:
        return package.install.install_package_name, {
            'name': params['name'],
            'activate': activate,
        }
    else:
        return None, None


async def expect_json(request: web.Request, validator: cerberus.Validator) -> Dict:
    try:
        jsn = await request.json()
    except json.JSONDecodeError:
        raise errors.ValidationError('Request does not appear to be json')
    if not validator.validate(jsn):
        raise errors.ValidationError('Input failed to validate', data=validator.errors)
    return validator.document


def make_request_info(method: str):
    return {
        'timestamp': time.time(),
        'method': method,
    }
