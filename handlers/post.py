from aiohttp_session import get_session
from .exception import InvalidRequest
# Using Python's typing to help auto-completion and refactor
from models import Post
import asyncio


async def post_publish(data, request):
    post: Post = request.app.models.post
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    await post.publish(data.get('title'), session['uid'], data['path'], data.get('categories'),\
                       data.get('tags'), data.get('content'), data.get('image'), data.get('excerpt'))

async def post_unpublish(data, request):
    post: Post = request.app.models.post
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    if str((await post.info(data, {'owner': True}))['owner']) != session['uid']:
        raise InvalidRequest('Permission denied')
    return await post.unpublish(data)

async def post_list(data, request):
    post: Post = request.app.models.post
    return await post.list(data.get('owner'), data.get('category'))

async def post_update(data, request):
    post: Post = request.app.models.post
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    if 'id' not in data:
        raise InvalidRequest('Post id required')
    if str((await post.info(data['id'], {'owner': True}))['owner']) != session['uid']:
        raise InvalidRequest('Permission denied')
    return await post.update(data)

async def post_info(data, request):
    post: Post = request.app.models.post
    return await post.info(data['id'])

async def post_search(data, request):
    post: Post = request.app.models.post
    return await post.search(data['content'])

async def post_info_subscribe(data, request, session):
    if 'id' not in data:
        raise InvalidRequest('Post id required')
    fu = asyncio.Future()
    async def send_update(post_parameter):
        if data['id'] == post_parameter['id']:
            session.send({data['id']: 'update'})
    async def send_remove(post_parameter):
        if data['id'] == post_parameter['id']:
            fu.set_exception(InvalidRequest("Post removed"))
    request.app.models.event.add_event_listener('post-update', send_update)
    request.app.models.event.add_event_listener('post-remove', send_remove)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener('post-update', send_update)
        request.app.models.event.remove_event_listener('post-remove', send_remove)

async def post_list_subscribe(data, request, session):
    fu = asyncio.Future()
    async def send_add(post_parameter):
        session.send({post_parameter['id']: 'add'})
    async def send_update(post_parameter):
        session.send({post_parameter['id']: 'update'})
    async def send_remove(post_parameter):
        session.send({post_parameter['id']: 'remove'})
    request.app.models.event.add_event_listener('post-add', send_add)
    request.app.models.event.add_event_listener('post-update', send_update)
    request.app.models.event.add_event_listener('post-remove', send_remove)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener('post-add', send_add)
        request.app.models.event.remove_event_listener('post-update', send_update)
        request.app.models.event.remove_event_listener('post-remove', send_remove)

handlers = {
    'post-publish': (post_publish, ('ajax-post',)),
    'post-unpublish': (post_unpublish, ('ajax-delete',)),
    'post-list': (post_list, ('ajax-get',)),
    'post-update': (post_update, ('ajax-post',)),
    'post-info': (post_info, ('ajax-get', 'ws')),
    'post-search': (post_search, ('ajax-get',)),
    'post-info-subscribe': (post_info_subscribe, ('ws',)),
    'post-list-subscribe': (post_list_subscribe, ('ws',)),
}
