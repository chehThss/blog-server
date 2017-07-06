from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId


class PostCategories:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['post_categories']
        self.event = models.event

    async def startup(self):
        await self.db.find_one_and_update(
            {'name': '$root'},
            {'$set': {'parent': None, 'children': []}},
            upsert=True
        )
        await self.db.create_index('name')

    async def add(self, name, parent):
        if await self.db.find_one({'name': name}) is not None:
            raise InvalidRequest(name + ' already exists')
        if parent is None:
            parent = '$root'
        if await self.db.find_one_and_update(
            {'name': parent},
            {'$addToSet': {'children': name}}
        ) is None:
            raise InvalidRequest(parent + ' does not exists')
        await self.db.insert_one({
            'name': name,
            'parent': parent,
            'children': []
        })

    async def get(self, name):
        result = await self.db.find_one({'name': name})
        if result is not None:
            result['_id'] = str(result['_id'])
        return result

    async def info(self, cid):
        result = await self.db.find_one({'_id': ObjectId(cid)})
        if '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    async def remove_children(self, name):
        result = await self.db.find_one({'name': name})
        children = result.get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'name': name})
        self.event.emit("category-remove", {'id': result['id']})

    async def remove(self, name):
        if name == '$root':
            raise InvalidRequest('Permission denied')
        result = await self.db.find_one({'name': name})
        if result is None:
            raise InvalidRequest(name + ' does not exist')
        children = result.get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'name': name})
        await self.db.find_one_and_update(
            {'name': result['parent']},
            {'$pullAll': {'children': [name]}}
        )
        self.event.emit("category-remove", {'id': result['id']})

    async def __check_change_name(self, name, new_name):
        if name == '$root':
            raise InvalidRequest('Permission denied')
        if await self.db.find_one({'name': name}) is None:
            raise InvalidRequest(name + ' does not exist')
        if await self.db.find_one({'name': new_name}) is not None:
            raise InvalidRequest(new_name + ' already exists')

    async def __update_name(self, name, new_name):
        result = await self.db.find_one({'name': name})
        await self.db.find_one_and_update(
            {'name': result['parent']},
            {'$pullAll': {'children': [name]}}
        )
        await self.db.find_one_and_update(
            {'name': result['parent']},
            {'$addToSet': {'children': new_name}}
        )
        await self.db.find_one_and_update(
            {'name': name},
            {'$set': {'name': new_name}}
        )
        if result['children'] is not None:
            for x in result['children']:
                await self.db.find_one_and_update(
                    {'name': x},
                    {'$set': {'parent': new_name}}
                )

    async def __check_change_parent(self, name, new_parent):
        if name == '$root':
            raise InvalidRequest('Permission denied')
        if await self.db.find_one({'name': name}) is None:
            raise InvalidRequest(name + ' does not exist')
        if await self.db.find_one({'name': new_parent}) is None:
            raise InvalidRequest(new_parent + ' does not exist')
        circle = new_parent
        while circle != '$root':
            if circle == name:
                raise InvalidRequest('Permission denied')
            circle = (await self.db.find_one({'name': circle}))['parent']

    async def __update_parent(self, name, new_parent):
        result = await self.db.find_one({'name': name})
        await self.db.find_one_and_update(
            {'name': result['parent']},
            {'$pullAll': {'children': [name]}}
        )
        await self.db.find_one_and_update(
            {'name': new_parent},
            {'$addToSet': {'children': name}}
        )
        await self.db.find_one_and_update(
            {'name': name},
            {'$set': {'parent': new_parent}}
        )

    async def update(self, name, new_name, parent):
        if parent is not None:
            await self.__check_change_parent(name, parent)
        if new_name is not None:
            await self.__check_change_name(name, new_name)
        if parent is not None:
            await self.__update_parent(name, parent)
        if new_name is not None:
            await self.__update_name(name, new_name)
