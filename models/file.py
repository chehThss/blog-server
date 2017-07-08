from os import path, makedirs, listdir
from shutil import rmtree, move
from handlers.exception import InvalidRequest
from aiohttp import web


class Repo:
    def __init__(self, models):
        self.upload_path = models.config['upload-path']
        makedirs(path.join(self.upload_path, 'site'), exist_ok=True)
        makedirs(path.join(self.upload_path, 'share'), exist_ok=True)
        makedirs(path.join(self.upload_path, 'private'), exist_ok=True)
        self.event = models.event
        self.event.on('user-add', self.init_for_user)
        self.event.on('user-remove', self.del_for_user)

    async def init_for_user(self, user):
        makedirs(path.join(self.upload_path, 'private', user['id'], 'public'), exist_ok=True)

    async def del_for_user(self, user):
        rmtree(path.join(self.upload_path, 'private', user['id']), ignore_errors=True)

    def resolve(self, p, user=None, mode=None):
        pathes = [i for i in p.split('/') if i]
        if mode is None:
            if len(pathes) == 0:
                raise InvalidRequest('Not found')
            if pathes[0] == 'site' or pathes[0] == 'share':
                return path.join(self.upload_path, *pathes)
            else:
                return path.join(self.upload_path, 'private', pathes[0], 'public', *pathes[1:])
        elif mode == 'private':
            if user is None:
                raise InvalidRequest('Login required')
            else:
                return path.join(self.upload_path, 'private', user, *pathes)
        elif mode == 'site' or mode == 'share':
            return path.join(self.upload_path, mode, *pathes)
        else:
            raise InvalidRequest('Unknown path')

    @staticmethod
    def send(p, type=None):
        if path.isdir(p) and (type is None or type == 'dir'):
            result = {}
            for k in listdir(p):
                if not k.startswith('.'):
                    result[k] = path.isdir(path.join(p, k))
            return result
        elif path.isfile(p) and (type is None or type == 'file'):
            return web.FileResponse(p, chunk_size=256*1024)
        else:
            raise InvalidRequest('Not found', status_code=404)

    @staticmethod
    def move_file(file, p):
        d = path.dirname(p)
        makedirs(d, exist_ok=True)
        move(file, p)
