from models import PostCategories, User
from .exception import InvalidRequest
from aiohttp_session import get_session


async def category_add(data, request):
    post_category: PostCategories = request.app.models.post_categories
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    return await post_category.add(data.get('name'), data.get('parent'))

async def category_get(data, request):
    post_category: PostCategories = request.app.models.post_categories
    return await post_category.get(data['name'])

async def category_remove(data, request):
    post_category: PostCategories = request.app.models.post_categories
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    await post_category.remove(data)

async def category_update(data, request):
    pass

handlers = {
    'category-add': (category_add, ('ajax-post',)),
    'category-get': (category_get, ('ajax-get',)),
    'category-remove': (category_remove, ('ajax-delete',)),
    'category-update': (category_update, ('ajax-post',)),
}
