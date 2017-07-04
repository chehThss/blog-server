from aiohttp_session import get_session
from .exception import InvalidRequest
from os import path, makedirs, listdir
from aiohttp import web
from shutil import move

async def file_put(data, request):
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    repo_path = path.join(request.app.config['upload-path'], session['uid'])
    file_path: str = data['path']
    if file_path.startswith('/'):
        file_path = '.' + file_path
    file_path = path.join(repo_path, file_path)
    if 'file' in data:
        file: web.FileField = data['file']
        filename: str = data['name'] if 'name' in data else file.filename
        if not path.isdir(file_path):
            makedirs(file_path)
        move(file.file, path.join(file_path, filename))
    else:
        if not path.isdir(file_path):
            makedirs(file_path)

async def file_get(data, request):
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    repo_path = path.join(request.app.config['upload-path'], session['uid'])
    if not path.isdir(repo_path):
        makedirs(repo_path)
    file = data['file']
    if file.startswith('/'):
        file = '.' + file
    file = path.join(request.app.config['upload-path'], session['uid'], file)
    if path.isdir(file):
        result = {}
        for k in listdir(file):
            if not k.startswith('.'):
                result[k] = path.isdir(path.join(file, k))
        return result
    if not path.isfile(file):
        raise web.HTTPNotFound
    return web.FileResponse(file, chunk_size=256*1024)

handlers = {
    'file-put': (file_put, ('ajax-post',)),
    'file-get': (file_get, ('ajax-get',))
}
