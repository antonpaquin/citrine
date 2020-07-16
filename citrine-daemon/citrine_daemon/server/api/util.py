import json
import time
from typing import *

from aiohttp import web
import cerberus

from citrine_daemon import errors


__all__ = [
    'make_request_info',
    'get_formdata',
    'expect_json',
]


def make_request_info(method: str):
    return {
        'timestamp': time.time(),
        'method': method,
    }


async def get_formdata(request: web.Request) -> Dict:
    res = {}
    async for formdata in await request.multipart():
        res[formdata.name] = await formdata.read()
    return res


async def expect_json(request: web.Request, validator: cerberus.Validator) -> Dict:
    try:
        jsn = await request.json()
    except json.JSONDecodeError:
        raise errors.ValidationError('Request does not appear to be json')
    if not validator.validate(jsn):
        raise errors.ValidationError('Input failed to validate', data=validator.errors)
    return validator.document

