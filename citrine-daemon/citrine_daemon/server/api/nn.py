import json
import logging

from aiohttp import web
import numpy as np

from citrine_daemon import core, errors
from citrine_daemon.server.parallel import AsyncFuture, run_async

from .aio_server import AioServer
from .util import make_request_info


logger = logging.getLogger(__name__)


def get_nn_server():
    server = AioServer()
    
    server.route(web.post, '/run/{package_name}/{function_name}', run_network, async_=True)
    server.route(web.post, '/_run/{package_name}/{model_name}', run_network_raw, async_=True)
    
    return server


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

    return run_async(core.call, kwargs={
        'package_name': request.match_info['package_name'],
        'function_name': request.match_info['function_name'],
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

    return run_async(core.call_raw, kwargs={
        'package_name': request.match_info['package_name'],
        'model_name': request.match_info['model_name'],
        'inputs': model_args,
    }, request_info=make_request_info('_run'))
