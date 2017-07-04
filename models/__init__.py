from motor import motor_asyncio
from .user import User
from .post import Post

class Models:
    def __init__(self, db: motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.user = User(db)
        self.post = Post(db)

    async def startup(self):
        await self.user.startup()
        await self.post.startup()