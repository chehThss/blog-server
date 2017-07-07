from models import PostCategories, User
from .exception import InvalidRequest
from aiohttp_session import get_session
import asyncio


async def category_add(data, request):
    post_category: PostCategories = request.app.models.post_categories
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    if 'name' not in data:
        raise InvalidRequest('Category cannot be empty')
    return await post_category.add(data.get('name'), data.get('parent'))

async def category_get_id(data, request):
    post_category: PostCategories = request.app.models.post_categories
    return await post_category.get_id(data.get('name'))

async def category_info(data, request):
    post_category: PostCategories = request.app.models.post_categories
    return await post_category.info(data.get('id'))

async def category_remove(data, request):
    post_category: PostCategories = request.app.models.post_categories
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    await post_category.remove(data)

async def category_update(data, request):
    post_category: PostCategories = request.app.models.post_categories
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    if 'id' not in data:
        raise InvalidRequest('Category cannot be empty')
    await post_category.update(data['id'], data.get('name'), data.get('parent'))

async def category_info_subscribe(data, request, session):
    if 'id' not in data or not (await request.app.models.post_categories.exist(data['id'])):
        raise InvalidRequest('Category does not exist')
    fu = asyncio.Future()
    async def send_update(category_parameter):
        if data['id'] == category_parameter['id']:
            session.send({category_parameter['id']: 'update'})
    async def send_remove(category_parameter):
        if data['id'] == category_parameter['id']:
            session.send({data['id']: 'remove'})
            fu.set_exception(InvalidRequest('Category removed'))
    request.app.models.event.add_event_listener('category-update', send_update)
    request.app.models.event.add_event_listener('category-remove', send_remove)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener('category-update', send_update)
        request.app.models.event.remove_event_listener('category-remove', send_remove)


async def category_list_subscribe(data, request, session):
    fu = asyncio.Future()
    async def send_add(category_parameter):
        session.send({category_parameter['id']: 'add'})
    async def send_update(category_parameter):
        session.send({category_parameter['id']: 'update'})
    async def send_remove(category_parameter):
        session.send({category_parameter['id']: 'remove'})
    request.app.models.event.add_event_listener('category-add', send_add)
    request.app.models.event.add_event_listener('category-update', send_update)
    request.app.models.event.add_event_listener('category-remove', send_remove)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener('category-add', send_add)
        request.app.models.event.remove_event_listener('category-update', send_update)
        request.app.models.event.remove_event_listener('category-remove', send_remove)

handlers = {
    'category-add': (category_add, ('ajax-post',)),
    'category-get-id': (category_get_id, ('ajax-get',)),
    'category-info': (category_info, ('ajax-get',)),
    'category-remove': (category_remove, ('ajax-delete',)),
    'category-update': (category_update, ('ajax-post',)),
    'category-info-subscribe': (category_info_subscribe, ('ws',)),
    'category-list-subscribe': (category_list_subscribe, ('ws',)),
}
