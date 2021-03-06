from motor import motor_asyncio
from pymongo import IndexModel, TEXT, DESCENDING
from time import time
from handlers.exception import InvalidRequest
from bson import ObjectId, Regex
import re


class Post:
    def __init__(self, models):
        self._db: motor_asyncio.AsyncIOMotorCollection = models.db['post']
        self.event = models.event

    async def startup(self):
        index_date = IndexModel([('date', DESCENDING)])
        index_text = IndexModel([('content', TEXT)])
        await self._db.create_indexes([index_date, index_text])

    async def publish(self, data):
        result = await self._db.insert_one({
            'title': data['title'],
            'owner': data['owner'],
            'path': data['path'],
            'absolute_path': data['absolute_path'],
            'date': time(),
            'categories': data.get('categories'),
            'tags': data.get('tags'),
            'image': data.get('image'),
            'excerpt': data.get('excerpt'),
            'content': data.get('content')
        })
        self.event.emit('post-add', {
            'id': str(result.inserted_id)
        })
        return str(result.inserted_id)

    async def unpublish(self, pid):
        if await self._db.find_one_and_delete({'_id': ObjectId(pid)}) is None:
            raise InvalidRequest('Post does not exist')
        self.event.emit('post-remove', {
            'id': pid
        })

    async def list(self, owner, category):
        result = []
        if owner is None and category is None:
            async for record in self._db.find():
                result.append(str(record['_id']))
            return result
        if owner:
            async for record in self._db.find({'owner': owner}):
                result.append(str(record['_id']))
        if category:
            async for record in self._db.find({'categories': {'$in': [category]}}):
                result.append(str(record['_id']))
        return result

    async def update(self, data):
        ls = ['title', 'path', 'absolute_path', 'categories', 'tags', 'image', 'excerpt', 'content']
        data_pre = await self._db.find_one({'_id': ObjectId(data['id'])})
        if data_pre is None:
            raise InvalidRequest('Post does not exist')
        for x in ls:
            if data.get(x) is not None:
                # TODO: check the data
                data_pre[x] = data[x]
        await self._db.find_one_and_update({'_id': ObjectId(data['id'])}, {'$set': {
            'title': data_pre['title'],
            'path': data_pre['path'],
            'absolute_path': data_pre['absolute_path'],
            'date': time(),
            'categories': data_pre['categories'],
            'tags': data_pre['tags'],
            'image': data_pre['image'],
            'excerpt': data_pre['excerpt'],
            'content': data_pre['content']
        }})
        self.event.emit('post-update', {
            'id': data['id']
        })

    async def info(self, pid, projection=None):
        if projection is None:
            projection = {
                '_id': False,
                'title': True,
                'owner': True,
                'path': True,
                'date': True,
                'categories': True,
                'tags': True,
                'image': True,
                'excerpt': True,
            }
        result = await self._db.find_one({'_id': ObjectId(pid)}, projection=projection)
        if result is None:
            raise InvalidRequest('Post does not exist')
        if '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    async def search(self, content):
        result = []
        async for record in self._db.find({'$text': {'$search': content}}):
            result.append(str(record['_id']))
        return result

    async def exist(self, pid):
        if await self._db.find_one({'_id': pid}) is None:
            return False
        return True

    async def find_files_in_directory(self, path):
        result = []
        pattern = re.compile('^' + re.escape(path))
        regex = Regex.from_native(pattern)
        regex.flags ^= re.UNICODE
        async for record in self._db.find({'absolute_path': {'$regex': regex}}):
            result.append(str(record['_id']))
        return result
