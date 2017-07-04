from motor import motor_asyncio
from pymongo import IndexModel, TEXT, DESCENDING
from time import time
from handlers.exception import InvalidRequest
from bson import ObjectId

class Post:
    def __init__(self, models):
        self._db: motor_asyncio.AsyncIOMotorCollection = models.db['post']

    async def startup(self):
        index_date = IndexModel([('date', DESCENDING)])
        index_text = IndexModel([('content', TEXT)])
        await self._db.create_indexes([index_date, index_text])

    async def publish(self, title, owner, path, categories, tags, content, image = None, excerpt = None):
        await self._db.insert_one({
            'title': title,
            'owner': owner,
            'path': path,
            'date': time(),
            'categories': categories,
            'tags': tags,
            'image': image,
            'excerpt': excerpt,
            'content': content
        })

    async def unpublish(self, pid):
        if await self._db.find_one_and_delete({'_id': ObjectId(pid)}) is None:
            raise InvalidRequest('Post does not exist')

    async def list(self):
        result = []
        async for record in self._db.find():
            result.append(str(record['_id']))
        return result

    async def update(self, data):
        all_data = await self._db.find_one({'_id': ObjectId(data['id'])})
        if all_data is None:
            raise InvalidRequest('Post does not exist')
        for x in data.keys():
            all_data[x] = data[x]
        await self._db.find_one_and_update({'_id': ObjectId(data['id'])}, {'$set': {
            'title': all_data['title'],
            'owner': all_data['owner'],
            'path': all_data['path'],
            'date': time(),
            'categories': all_data['categories'],
            'tags': all_data['tags'],
            'image': all_data['image'],
            'excerpt': all_data['excerpt'],
            'content': all_data['content']
        }})

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
