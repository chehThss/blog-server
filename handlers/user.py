from aiohttp_session import get_session
from .exception import InvalidRequest
# Using Python's typing to help auto-completion and refactor
from models import User

ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'

async def user_add(data, request):
    user: User = request.app.models.user
    # TODO: check input
    return await user.add(data['username'], data['password'], ROLE_EDITOR)

async def user_info(data, request):
    user: User = request.app.models.user
    # TODO: check input
    return await user.info(data['id'])

async def user_remove(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    # TODO: check input
    if data != session['uid'] or (await user.info(session['uid'], {'role': True}))['role'] != ROLE_ADMIN:
        raise InvalidRequest('Permission denied')
    return await user.remove(data)

async def check_session(data, request):
    session = await get_session(request)
    return session.get('uid')

async def login(data, request):
    user: User = request.app.models.user
    # TODO: check input
    user_id = await user.check_user(data['username'], data['password'])
    session = await get_session(request)
    session['uid'] = user_id
    return user_id

async def logout(data, request):
    session = await get_session(request)
    if 'uid' in session:
        del session['uid']
    else:
        raise InvalidRequest('User already logout')

async def user_set_password(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    if data['id'] != session['uid']:
        raise InvalidRequest('Permission denied')
    await user.set_password(data['id'], data['password'])
    # TODO: sign out other devices

handlers = {
    'user-add': (user_add, ('ajax-post', 'ws')),
    'user-info': (user_info, ('ajax-get', 'ws')),
    'user-remove': (user_remove, ('ajax-delete', 'ws')),
    'login': (login, ('ajax-post', 'ws')),
    'logout': (logout, ('ajax-get', 'ws')),
    'check-session': (check_session, ('ajax-get', 'ws')),
    'user-set-password': (user_set_password, ('ajax-post')),
}

