from motor import motor_asyncio


class PostCategories:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['post_categories']

    async def startup(self):
        await self.db.find_one_and_update(
            {'name': '$root'},
            {'$set': {'parent': None}},
            upsert=True
        )
        await self.db.create_index('name')
