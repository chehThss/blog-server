import json
from inspect import signature
from typing import Dict, Callable
from aiohttp import web
from handlers import handlers, InvalidRequest
from .parse import parse

ajax_get_handlers: Dict[str, Callable] = dict()
ajax_post_handlers: Dict[str, Callable] = dict()
ajax_put_handlers: Dict[str, Callable] = dict()
ajax_delete_handlers: Dict[str, Callable] = dict()
ajax_patch_handlers: Dict[str, Callable] = dict()

global_handlers: Dict[str, Dict[str, Callable]] = {
    web.hdrs.METH_GET: ajax_get_handlers,
    web.hdrs.METH_POST: ajax_post_handlers,
    web.hdrs.METH_PUT: ajax_put_handlers,
    web.hdrs.METH_DELETE: ajax_delete_handlers,
    web.hdrs.METH_PATCH: ajax_patch_handlers
}

for n, (h, p) in handlers.items():
    if 'ajax-get' in p:
        ajax_get_handlers[n] = h
    if 'ajax-post' in p:
        ajax_post_handlers[n] = h
    if 'ajax-put' in p:
        ajax_put_handlers[n] = h
    if 'ajax-delete' in p:
        ajax_delete_handlers[n] = h
    if 'ajax-patch' in p:
        ajax_patch_handlers[n] = h

async def ajax_handler(request: web.Request):
    action = request.match_info.get('action')
    data = await parse(request, global_handlers.keys())
    if action not in global_handlers[request.method]:
        raise web.HTTPBadRequest()
    handler = global_handlers[request.method][action]
    try:
        result = await handler(*(data, request, None)[:len(signature(handler).parameters)])
    except InvalidRequest as err:
        return web.Response(text=json.dumps({
            'status': 1,
            'data': str(err)
        }, ensure_ascii=False), status=err.status_code, content_type='application/json')
    if isinstance(result, web.StreamResponse):
        return result
    return web.Response(text=json.dumps({
        'status': 0,
        **({'data': result} if result is not None else {})
    }, ensure_ascii=False), content_type='application/json')
