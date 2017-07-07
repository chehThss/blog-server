from motor import motor_asyncio


class Settings:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['settings']
        self.event = models.event

    async def startup(self):
        await self.db.create_index('key')

    async def get(self):
        result = {}
        async for record in self.db.find():
            result[record['key']] = record['value']
        return result

    async def set(self, data):
        for x in data.keys():
            self.db.find_one_and_update(
                {'key': x},
                {'$set': {'value': data[x]}},
                upsert=True
            )
            self.event.emit('settings-update', {
                'key': x,
                'value': data[x]
            })
