from motor import motor_asyncio
from handlers.exception import InvalidRequest


class PostCategories:
    def __init__(self, models):
        self.db: motor_asyncio.AsyncIOMotorCollection = models.db['post_categories']

    async def startup(self):
        await self.db.find_one_and_update(
            {'name': '$root'},
            {'$set': {'parent': None}},
            upsert=True
        )
        await self.db.create_index('name')

    async def add(self, name, parent):
        if await self.db.find_one({'name': name}) is not None:
            raise InvalidRequest('Category already exists')
        if parent is None:
            parent = '$root'
        if await self.db.find_one_and_update(
            {'name': parent},
            {'$addToSet': {'children': name}}
        ) is None:
            raise InvalidRequest('Parent does not exists')
        await self.db.insert_one({
            'name': name,
            'parent': parent
        })

    async def get(self, name):
        return await self.db.find_one({'name': name}, projection={
            '_id': False
        })

    async def remove_children(self, name):
        children = (await self.db.find_one({'name': name})).get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'name': name})

    async def remove(self, name):
        result = await self.db.find_one({'name': name})
        if result is None:
            raise InvalidRequest('Category does not exist')
        children = result.get('children')
        if children is not None:
            for x in children:
                await self.remove_children(x)
        await self.db.find_one_and_delete({'name': name})
        await self.db.find_one_and_update(
            {'name': result['parent']},
            {'$pullAll': {'children': [name]}}
        )
