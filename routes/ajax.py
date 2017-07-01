from aiohttp import web
from urllib.parse import parse_qs
from typing import Dict, Tuple, Callable, Any
from inspect import signature
from . import handlers
import json

ajax_get_handlers: Dict[str, Callable] = {}
ajax_post_handlers: Dict[str, Callable] = {}

for n, (h, p) in handlers.handlers.items():
    if 'ajax-get' in p:
        ajax_get_handlers[n] = h
    if 'ajax-post' in p:
        ajax_post_handlers[n] = h

async def ajax_get(request):
    action = request.match_info.get('action')
    if action not in ajax_get_handlers:
        return web.HTTPBadRequest()
    data = parse_qs(request.query_string)
    try:
        handler = ajax_get_handlers[action]
        result = await handler(*(data, request)[:len(signature(handler).parameters)])
        return web.Response(text=json.dumps(result, ensure_ascii=False), content_type='application/json')
    except handlers.InvalidRequest as err:
        return web.HTTPBadRequest()
    except:
        return web.HTTPInternalServerError()

async def ajax_post(request):
    pass
