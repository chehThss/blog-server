from motor import motor_asyncio


class User:
    def __init__(self, db: motor_asyncio.AsyncIOMotorDatabase):
        self._db: motor_asyncio.AsyncIOMotorCollection = db['user']

    async def add(self, username, password, role):
        return str((await self._db.insert_one({
            'user': username,
            'password': password,
            'role': role

        })).inserted_id)

