import json
import logging
from typing import *

from aiohttp import web
import cerberus

from citrine_daemon import errors, package
from citrine_daemon.server.parallel import AsyncFuture, run_async

from .aio_server import AioServer
from .util import expect_json, make_request_info, get_formdata


logger = logging.getLogger(__name__)


def get_package_server():
    server = AioServer()

    server.route(web.post, '/fetch', package_fetch, async_=True)
    server.route(web.post, '/install', package_install, async_=True)
    server.route(web.post, '/activate', package_activate, async_=True)
    server.route(web.post, '/deactivate', package_deactivate, async_=True)
    server.route(web.post, '/remove', package_remove, async_=True)
    server.route(web.post, '/search', package_search, async_=True)
    server.route(web.get,  '/list', package_list, async_=True)

    return server


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


async def package_fetch(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, but don't load / run any code
    """
    logger.debug('Handling request for method package.fetch')
    params = await package_install_spec(request)
    install_fn, kwargs = package_install_command(params, activate=True)
    if install_fn is None:
        raise errors.InternalError('Invalid package spec made it through validation')
    return run_async(install_fn, kwargs=kwargs, request_info=make_request_info('package.fetch'))


async def package_install(request: web.Request) -> AsyncFuture:
    """
    Fetch means download and put in DB, then load the module and make it available
    """
    logger.debug('Handling request for method package.install')
    params = await package_install_spec(request)
    install_fn, kwargs = package_install_command(params, activate=True)
    if install_fn is None:
        raise errors.InternalError('Invalid package spec made it through validation')
    return run_async(install_fn, kwargs=kwargs, request_info=make_request_info('package.install'))


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


async def package_search(request: web.Request) -> AsyncFuture:
    logger.debug('Handling request for method package.search')
    validator = cerberus.Validator(schema={
        'query': {
            'type': 'string',
            'required': True,
        },
    })
    params = await expect_json(request, validator)
    return run_async(package.repo.search_package, kwargs={
        'query': params['query'],
    }, request_info=make_request_info('package.list'))
