from aiohttp_session import get_session
from .exception import InvalidRequest
from os import path, makedirs
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
    file = request.app.models.file
    mode = data.get('mode')
    if mode == 'private':
        session = await get_session(request)
        if 'uid' not in session:
            raise InvalidRequest('Login required')
        p = file.resolve(data['path'], session['uid'], mode)
        return file.send(p, allow_dir=True)
    else:
        p = file.resolve(data['path'], mode=mode)
        return file.send(p, allow_dir=(mode == 'share'))

handlers = {
    'file-get': (file_get, ('file-get',))
}
