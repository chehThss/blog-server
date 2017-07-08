from aiohttp_session import get_session
from .exception import InvalidRequest
from os import path, makedirs, remove
from shutil import move, rmtree

async def file_get(data, request):
    file = request.app.models.file
    mode = data.get('mode')
    type = data.get('type')
    if mode == 'private':
        session = await get_session(request)
        if 'uid' not in session:
            raise InvalidRequest('Login required')
        p = file.resolve(data['path'], session['uid'], mode)
        return file.send(p, type=type)
    else:
        p = file.resolve(data['path'], mode=mode)
        return file.send(p, type=type)

async def file_post(data, request):
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    mode = data.get('mode', 'private')
    type = data.get('type')
    file = request.app.models.file
    f = data.get('file')
    p = file.resolve(data['path'], session['uid'], mode)
    if f is None and (type is None or type == 'dir'):
        makedirs(p, exist_ok=True)
    elif f is not None and (type is None or type == 'file'):
        filename = data.get('name', f.filename)
        makedirs(p, exist_ok=True)
        move(f.file, path.join(p, filename))
    else:
        raise InvalidRequest('Cannot create file')

async def file_delete(data, request):
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    mode = data.get('mode', 'private')
    type = data.get('type')
    file = request.app.models.file
    p = file.resolve(data['path'], session['uid'], mode)
    if path.isfile(p) and (type is None or type == 'file'):
        remove(p)
    elif path.isdir(p) and (type is None or type == 'data'):
        rmtree(p, ignore_errors=True)
    else:
        raise InvalidRequest('Not found')


handlers = {
    'file-get': (file_get, ('file-get',)),
    'file-post': (file_post, ('file-post',)),
    'file-delete': (file_delete, ('file-delete',))
}
