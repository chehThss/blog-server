import json
from aiohttp import web
from handlers import handlers, InvalidRequest
from typing import Dict, Callable
from .parse import parse, ALL_METHODS
from inspect import signature

global_handlers: Dict[str, Callable] = {}
for n, (h, p) in handlers.items():
    for i in p:
        if i.startswith('file-'):
            method = i[5:].upper()
            if method not in ALL_METHODS:
                raise RuntimeError('Unknown method')
            global_handlers[method] = h

async def file_handler(request: web.Request):
    path = '/file' + request.match_info.get('path')
    data = await parse(request, global_handlers.keys())
    data['path'] = path
    handler = global_handlers[request.method]
    try:
        result = await handler(*(data, request, None)[:len(signature(handler).parameters)])
    except InvalidRequest as err:
        return web.Response(text=json.dumps({
            'status': 1,
            'data': str(err)
        }, ensure_ascii=False),status=err.status_code, content_type='application/json')
    if isinstance(result, web.StreamResponse):
        return result
    return web.Response(text=json.dumps({
        'status': 0,
        **({'data': result} if result is not None else {})
    }, ensure_ascii=False), content_type='application/json')
