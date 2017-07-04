from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId

class User:
    def __init__(self, db: motor_asyncio.AsyncIOMotorDatabase):
        self._db: motor_asyncio.AsyncIOMotorCollection = db['user']

    async def startup(self):
        await self._db.create_index('user')

    async def add(self, username, password, role):
        if await self._db.find_one({'user': username}) is not None:
            raise InvalidRequest('User already exists')
        return str((await self._db.insert_one({
            'user': username,
            'password': password,
            'role': role
        })).inserted_id)

    async def info(self, uid, projection=None):
        if projection is None:
            projection = {
                '_id': False,
                'user': True,
                'avatar': True,
                'role': True
            }
        result = await self._db.find_one({'_id': ObjectId(uid)}, projection=projection)
        if result is None:
            raise InvalidRequest('User does not exist')
        if '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    async def remove(self, uid):
        if await self._db.find_one_and_delete({'_id': ObjectId(uid)}) is None:
            raise InvalidRequest('User does not exist')

    async def check_user(self, username, psw):
        result = await self._db.find_one({'user': username}, projection = {
            'password': True,
            '_id': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        if result['password'] != psw:
            raise InvalidRequest('Wrong password')
        return str(result['_id'])

    async def list(self):
        result = []
        async for record in self._db.find():
            result.append(str(record['_id']))
        return result

    async def role(self, uid):
        result = await self._db.find_one({'_id': ObjectId(uid)}, projection = {
            'role': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        return result['role']

    async def set_role(self, uid, role):
        result = await self._db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'role': role}}
        )
        if result is None:
            raise InvalidRequest('User does not exist')

    async def set_password(self, uid, password):
        if await self._db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'password': password}}
        ) is None:
            raise InvalidRequest('User does not exist')