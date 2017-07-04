from motor import motor_asyncio
from .user import User
from .event import Event


class Models:
    def __init__(self, db: motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.event = Event()
        self.user = User(self)

    async def startup(self):
        await self.user.startup()
