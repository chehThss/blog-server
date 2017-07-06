from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId
from .event import Event


ROLE_ROOT = 'root'
ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'


class User:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['user']
        self.event: Event = models.event
        self.__root_id = ''

    async def startup(self):
        root = (await self.db.find_one_and_update(
            {'user': ROLE_ROOT},
            {'$set': {'password': 'root', 'role': 'administrator'}},
            upsert=True
        ))
        if root is None:
            self.__root_id = str((await self.db.find_one({'user': ROLE_ROOT}))['_id'])
        else:
            self.__root_id = str(root.get('_id'))
        self.event.emit('user-add', {
            'id': self.__root_id,
            'user': 'root'
        })
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

    async def get_id(self, username):
        result = await self.db.find_one({'user': username})
        if result:
            return str(result['_id'])
        raise InvalidRequest('User does not exist')

    async def remove(self, uid):
        if uid == self.__root_id:
            raise InvalidRequest('Root cannot be removed')
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
        self.event.emit('user-update', {
            'id': uid,
            'user': result['user']
        })

    async def role(self, uid):
        result = await self.db.find_one({'_id': ObjectId(uid)}, projection={
            'role': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        return result['role']

    async def set_role(self, uid, role):
        if uid == self.__root_id:
            raise InvalidRequest('Permission denied')
        result = await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {'role': role}}
        )
        if result is None:
            raise InvalidRequest('User does not exist')
        self.event.emit('user-update', {
            'id': uid,
            'user': result['user']
        })

    async def update(self, uid, user, avatar, password):
        if uid == self.__root_id:
            raise InvalidRequest('Permission denied')
        user_pre = await self.db.find_one({'_id': ObjectId(uid)})
        if user_pre is None:
            raise InvalidRequest('User does not exist')
        if user is None:
            user = user_pre.get('user')
        if avatar is None:
            avatar = user_pre.get('avatar')
        if password is None:
            password = user_pre.get('password')
        await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {
                'user': user,
                'avatar': avatar,
                'password': password
            }})
        self.event.emit('user-update', {
            'id': uid,
            'user': user
        })

    async def is_administrator(self, uid):
        if (await self.info(uid, projection={'role': True}))['role'] == ROLE_ADMIN:
            return True
        else:
            return False
