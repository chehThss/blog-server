from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId
from .event import Event
import bcrypt


ROLE_ROOT = 'root'
ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'


class User:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['user']
        self.event: Event = models.event
        self.__root_id = ''

    async def startup(self):
        password = 'root'
        password = password.encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        root = await self.db.find_one({'user': ROLE_ROOT})
        if root is None:
            root = await self.db.insert_one({
                'user': ROLE_ROOT,
                'password': hashed,
                'role': 'administrator',
            })
            self.__root_id = str(root.inserted_id)
        else:
            self.__root_id = str(root['_id'])
        self.event.emit('user-add', {
            'id': self.__root_id,
            'user': 'root'
        })
        await self.db.create_index('user')

    async def add(self, username, password, role):
        if await self.db.find_one({'user': username}) is not None:
            raise InvalidRequest('User already exists')
        password = password.encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        result = await self.db.insert_one({
            'user': username,
            'password': hashed,
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
        if result is None:
            raise InvalidRequest('User does not exist')
        return str(result['_id'])

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

    async def check_user(self, username, password):
        result = await self.db.find_one({'user': username}, projection={
            'password': True,
            '_id': True
        })
        if result is None:
            raise InvalidRequest('User does not exist')
        password = password.encode('utf-8')
        if not bcrypt.checkpw(password, result['password']):
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
        if uid == self.__root_id and user is not None:
            raise InvalidRequest('Permission denied')
        user_pre = await self.db.find_one({'_id': ObjectId(uid)})
        if user_pre is None:
            raise InvalidRequest('User does not exist')
        if user is None:
            user = user_pre.get('user')
        if avatar is None:
            avatar = user_pre.get('avatar')
        if password is None:
            hashed = user_pre.get('password')
        else:
            password = password.encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        await self.db.find_one_and_update(
            {'_id': ObjectId(uid)},
            {'$set': {
                'user': user,
                'password': hashed,
                ** ({'avatar': avatar} if avatar is not None else {})
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

    async def exist(self, uid):
        if (await self.db.find_one({"_id": ObjectId(uid)})) is None:
            return False
        else:
            return True
