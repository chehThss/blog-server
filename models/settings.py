from motor import motor_asyncio


class Settings:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['user']

    async def startup(self):
        await self.db.create_index('key')