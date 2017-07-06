import os
import json
import tempfile
from aiohttp import web
from urllib.parse import parse_qs

POST_METHODS = {web.hdrs.METH_PATCH, web.hdrs.METH_POST, web.hdrs.METH_PUT,
                web.hdrs.METH_TRACE, web.hdrs.METH_DELETE}

ALL_METHODS = POST_METHODS | {web.hdrs.METH_GET}

async def parse(request: web.Request, methods=ALL_METHODS):
    if request.method not in methods:
        raise web.HTTPMethodNotAllowed(request.method, list(methods))
    if request.method == web.hdrs.METH_GET:
        data = parse_qs(request.query_string)
        for k in data.keys():
            if len(data[k]):
                data[k] = data[k][0]
            else:
                del data[k]
    elif request.method in POST_METHODS:
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
    else:
        raise web.HTTPMethodNotAllowed(request.method, list(methods))
    return data
