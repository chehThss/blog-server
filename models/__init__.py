from motor import motor_asyncio
from .user import User


class Models:
    def __init__(self, db: motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.user = User(db)