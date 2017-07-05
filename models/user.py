from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId
from .event import Event


ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'


class User:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['user']
        self.event: Event = models.event

    async def startup(self):
        await self.db.find_one_and_update(
            {'user': 'root'},
            {'$set': {'password': 'root', 'role': 'administrator'}},
            upsert=True)
        await self.db.create_index('user')

    async def add(self, username, password, role):
        if await self.db.find_one({'user': username}) is not None:
            raise InvalidRequest('User already exists')
        result = await self.db.insert_one({
            'user': username,
            'password': password,
            'role': role
        })
        self.event.emit('user-add', {
            'id': str(result.inserted_id),
            'user': username
        })
        return str(result.inserted_id)

    async def info(self, uid, projection=None):
        if projection is None:
            projection = {
                '_id': False,
                'user': True,
                'avatar': True,
                'role': True
            }
        result = await self.db.find_one({'_id': ObjectId(uid)}, projection=projection)
        if result is None:
            raise InvalidRequest('User does not exist')
        if '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    async def remove(self, uid):
        result = await self.db.find_one_and_delete({'_id': ObjectId(uid)}, projection={'user': True})
        if result is None:
            raise InvalidRequest('User does not exist')
        self.event.emit('user-remove', {
            'id': uid,
            'user': result['user']
        })

    async def check_user(self, username, psw):
        result = await self.db.find_one({'user': username}, projection={
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
        async for record in self.db.find():
            result.append(str(record['_id']))
        return result

    async def get_settings(self, uid):
        result = await self.db.find_one({'_id': ObjectId(uid)})
        if result is None:
            raise InvalidRequest('User does not exist')
        return result.get('settings')

    async def set_settings(self, uid, settings):
        result = await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'settings': settings}}
        )
        if result is None:
            raise InvalidRequest('User does not exist')

    async def role(self, uid):
        result = await self.db.find_one({'_id': ObjectId(uid)}, projection={
            'role': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        return result['role']

    async def set_role(self, uid, role):
        result = await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'role': role}}
        )
        if result is None:
            raise InvalidRequest('User does not exist')

    async def set_password(self, uid, password):
        if await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'password': password}}
        ) is None:
            raise InvalidRequest('User does not exist')

    async def is_administrator(self, uid):
        if (await self.info(uid, projection={'role': True}))['role'] == ROLE_ADMIN:
            return True
        else:
            return False
