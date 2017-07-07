from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId


class PostCategories:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['post_categories']
        self.event = models.event
        self.root_id = ''

    async def startup(self):
        await self.db.find_one_and_update(
            {'name': '$root'},
            {'$set': {'parent': None}},
            upsert=True
        )
        self.root_id = str((await self.db.find_one({'name': '$root'}))['_id'])
        await self.db.create_index('name')

    async def add(self, name, parent):
        if await self.db.find_one({'name': name}) is not None:
            raise InvalidRequest('Category already exists')
        if parent is None:
            parent = self.root_id
        if await self.db.find_one({'_id': ObjectId(parent)}) is None:
            raise InvalidRequest('Parent does not exists')
        result = await self.db.insert_one({
            'name': name,
            'parent': parent,
            'children': []
        })
        self.event.emit('category-add', {
            'id': str(result.inserted_id)
        })
        self.db.find_one_and_update(
            {'_id': ObjectId(parent)},
            {'$addToSet': {'children': str(result.inserted_id)}}
        )
        self.event.emit('category-update', {
            'id': parent
        })
        return str(result.inserted_id)

    async def get_id(self, name):
        result = await self.db.find_one({'name': name})
        if result is None:
            raise InvalidRequest('Category does not exist')
        return str(result['_id'])

    async def info(self, cid):
        result = await self.db.find_one({'_id': ObjectId(cid)}, projection={
            '_id': False
        })
        if result is None:
            raise InvalidRequest("Category does not exist")
        return result

    async def remove_children(self, cid):
        result = await self.db.find_one({'_id': ObjectId(cid)})
        children = result.get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'_id': ObjectId(cid)})
        self.event.emit('category-remove', {
            'id': cid
        })

    async def remove(self, cid):
        if cid == self.root_id:
            raise InvalidRequest('Permission denied')
        result = await self.db.find_one({'_id': ObjectId(cid)})
        if result is None:
            raise InvalidRequest('Category does not exist')
        children = result.get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'_id': ObjectId(cid)})
        self.event.emit('category-remove', {
            'id': str(result['_id'])
        })
        parent = await self.db.find_one_and_update(
            {'_id': ObjectId(result['parent'])},
            {'$pullAll': {'children': [cid]}}
        )
        self.event.emit('category-update', {
            'id': str(parent['_id'])
        })

    async def __check_change_name(self, cid, new_name):
        if cid == self.root_id:
            raise InvalidRequest('Permission denied')
        if await self.db.find_one({'_id': ObjectId(cid)}) is None:
            raise InvalidRequest('Category does not exist')
        if await self.db.find_one({'name': new_name}) is not None:
            raise InvalidRequest(new_name + ' already exists')
        return True

    async def __update_name(self, cid, new_name):
        await self.db.find_one_and_update(
            {'_id': ObjectId(cid)},
            {'$set': {'name': new_name}}
        )
        self.event.emit('category-update', {
            'id': cid
        })

    async def __check_change_parent(self, cid, new_parent):
        if cid == self.root_id:
            raise InvalidRequest('Permission denied')
        if await self.db.find_one({'_id': ObjectId(cid)}) is None:
            raise InvalidRequest('Category does not exist')
        if await self.db.find_one({'_id': ObjectId(new_parent)}) is None:
            raise InvalidRequest('New parent does not exist')
        circle = new_parent
        while circle != self.root_id:
            if circle == cid:
                raise InvalidRequest('Permission denied')
            circle = (await self.db.find_one({'_id': ObjectId(circle)}))['parent']
        return True

    async def __update_parent(self, cid, new_parent):
        result = await self.db.find_one({'_id': ObjectId(cid)})
        parent_pre = await self.db.find_one_and_update(
            {'_id': ObjectId(result['parent'])},
            {'$pullAll': {'children': [cid]}}
        )
        self.event.emit('category-update', {
            'id': str(parent_pre['_id'])
        })
        parent_after = await self.db.find_one_and_update(
            {'_id': ObjectId(new_parent)},
            {'$addToSet': {'children': cid}}
        )
        self.event.emit('category-update', {
            'id': str(parent_after['_id'])
        })
        await self.db.find_one_and_update(
            {'_id': ObjectId(cid)},
            {'$set': {'parent': new_parent}}
        )
        self.event.emit('category-update', {
            'id': cid
        })

    async def update(self, cid, name, parent):
        if parent is not None:
            update_parent = await self.__check_change_parent(cid, parent)
        if name is not None:
            update_name = await self.__check_change_name(cid, name)
        if parent is not None and update_parent == True:
            await self.__update_parent(cid, parent)
        if name is not None and update_name == True:
            await self.__update_name(cid, name)

    async def exist(self, cid):
        if self.db.find_one({'_id': ObjectId(cid)}) is None:
            return False
        return True

