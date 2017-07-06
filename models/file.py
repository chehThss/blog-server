from os import path, makedirs
from shutil import rmtree


class Repo:
    def __init__(self, models):
        self.upload_path = models.config['upload-path']
        self.event = models.event
        self.event.on('user-add', self.init_for_user)
        self.event.on('user-remove', self.del_for_user)

    async def init_for_user(self, user):
        makedirs(path.join(self.upload_path, user['id']), exist_ok=True)

    async def del_for_user(self, user):
        rmtree(path.join(self.upload_path, user['id']))
