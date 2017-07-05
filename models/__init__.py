from motor import motor_asyncio
from .user import User
from .event import Event
from .file import Repo


class Models:
    def __init__(self, config):
        self.config = config
        self.client = motor_asyncio.AsyncIOMotorClient(self.config['db'])
        self.db = self.client.get_default_database()
        self.event = Event()
        self.user = User(self)
        self.file = Repo(self)

    async def startup(self):
        await self.user.startup()

    async def shutdown(self):
        self.client.close()
