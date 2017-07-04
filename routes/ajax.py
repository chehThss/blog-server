import os
import json
import tempfile
from inspect import signature
from typing import Dict, Callable
from urllib.parse import parse_qs
from aiohttp import web
from handlers import handlers, InvalidRequest

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
    if request.method == web.hdrs.METH_GET:
        data = parse_qs(request.query_string)
        for k in data.keys():
            if len(data[k]):
                data[k] = data[k][0]
            else:
                del data[k]
    elif request.method in {web.hdrs.METH_POST, web.hdrs.METH_PUT, web.hdrs.METH_DELETE, web.hdrs.METH_PATCH}:
        if request.content_type == 'application/x-www-form-urlencoded':
            charset = request.charset or 'utf-8'
            data = parse_qs((await request.read()).decode(charset), encoding=charset)
            for k in data.keys():
                if len(data[k]):
                    data[k] = data[k][0]
                else:
                    del data[k]
        elif request.content_type == 'application/json':
            try:
                charset = request.charset or 'utf-8'
                data = json.loads((await request.read()).decode(charset), encoding=charset)
            except json.JSONDecodeError:
                raise web.HTTPBadRequest()
        elif request.content_type == 'multipart/form-data':
            multipart = await request.multipart()
            field = await multipart.next()
            data = dict()
            while field is not None:
                size = 0
                content_type = field.headers.get(web.hdrs.CONTENT_TYPE)
                if field.filename:
                    fd, path = tempfile.mkstemp()
                    chunk = await field.read_chunk(size=2**16)
                    while chunk:
                        chunk = field.decode(chunk)
                        os.write(fd, chunk)
                        size += len(chunk)
                        chunk = await field.read_chunk(size=2**16)
                    os.close(fd)
                    data[field.name] = web.FileField(field.name, field.filename, path, content_type, field.headers)
                else:
                    value = await field.read(decode=True)
                    if content_type is None or content_type.startswith('text/'):
                        charset = field.get_charset(default='utf-8')
                        value = value.decode(charset)
                    data[field.name] = value
                    size += len(value)
                field = await multipart.next()
        else:
            raise web.HTTPBadRequest()
    elif request.method == web.hdrs.METH_OPTIONS:
        return web.Response()
    else:
        raise web.HTTPMethodNotAllowed(request.method, global_handlers.keys())
    if action not in global_handlers[request.method]:
        raise web.HTTPBadRequest()
    handler = global_handlers[request.method][action]
    try:
        result = await handler(*(data, request, None)[:len(signature(handler).parameters)])
    except InvalidRequest as err:
        return web.Response(text=json.dumps({
            'status': 1,
            'data': str(err)
        }, ensure_ascii=False), content_type='application/json')
    if isinstance(result, web.StreamResponse):
        return result
    return web.Response(text=json.dumps({
        'status': 0,
        **({'data': result} if result is not None else {})
    }, ensure_ascii=False), content_type='application/json')
