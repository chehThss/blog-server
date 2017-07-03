from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId
from pymongo import ReturnDocument

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
            'role': role,
            'login': False
        })).inserted_id)

    async def info(self, uid):
        result = await self._db.find_one({'_id': ObjectId(uid)}, projection={
            '_id': False,
            'user': True,
            'avatar': True,
            'role': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        return result

    async def remove(self, id):
        if await self._db.find_one_and_delete({'_id': ObjectId(id)}) is None:
            raise InvalidRequest('User does not exist')

    async def login(self, username, psw):
        result = await self._db.find_one({'user': username}, projection = {
            'password': True,
            'login': True,
            '_id': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        if(result['login']):
            raise InvalidRequest('User already login')
        if str(result['password']) != psw:
            raise InvalidRequest('Wrong password')
        else:
            await self._db.find_one_and_update(
                {'_id': result['_id']},
                {'$set': {'login': True}})
            return str(result['_id'])

    async def signout(self, id):
        result = await self._db.find_one_and_update(
            {'_id': ObjectId(id)},
            {'$set': {'login': False}},
            return_document = ReturnDocument.BEFORE)
        if result is None:
            raise InvalidRequest('User does not exist')
        if not result['login']:
            raise InvalidRequest("User already signs out")
