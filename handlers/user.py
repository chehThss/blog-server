from aiohttp_session import get_session
from .exception import InvalidRequest
# Using Python's typing to help auto-completion and refactor
from models import User
import asyncio


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

async def user_get_id(data, request):
    user: User = request.app.models.user
    # TODO: check input
    return await user.get_id(data['username'])

async def user_remove(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    # TODO: check input
    if data != session['uid'] and (await user.info(session['uid'], {'role': True}))['role'] != ROLE_ADMIN:
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

async def user_list(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    if (await user.info(session['uid'], {'role': True}))['role'] != ROLE_ADMIN:
        raise InvalidRequest('Permission denied')
    return await user.list()

async def user_get_settings(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    return await user.get_settings(session['uid'])

async def user_set_settings(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    return await user.set_settings(session['uid'], data['settings'])

async def user_set_role(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    if (await user.info(session['uid'], {'role': True}))['role'] != ROLE_ADMIN:
        raise InvalidRequest('Permission denied')
    return await user.set_role(data['id'], data['role'])

async def user_update(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    avatar = data.get('avatar')
    if avatar is not None:
        file = request.app.models.file
        f = avatar.file
        avatar = '/site/avatar/' + session['uid'] + '.jpeg'
        p = file.resolve(avatar)
        file.move_file(f, p)
    await user.update(session['uid'], data.get('username'), avatar, data.get('password'))

async def user_set_password(data, request):
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session:
        raise InvalidRequest('Login required')
    await user.update(session['uid'], None, None, data['password'])
    # TODO: sign out other devices

async def user_info_subscribe(data, request, session):
    fu = asyncio.Future()
    uid = data.get('id')
    if uid is None:
        sess = await get_session(request)
        uid = sess['uid']
    if not (await request.app.models.user.exist(uid)):
        raise InvalidRequest('User does not exist')
    async def send_update(user_parameter):
        if user_parameter['id'] == uid:
            session.send({user_parameter['id']: "update"})
    async def send_remove(user_parameter):
        if user_parameter['id'] == uid:
            session.send({uid: 'remove'})
            fu.set_exception(InvalidRequest("User removed"))
    request.app.models.event.add_event_listener("user-update", send_update)
    request.app.models.event.add_event_listener("user-remove", send_remove)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener("user-update", send_update)
        request.app.models.event.remove_event_listener("user-remove", send_remove)


async def user_list_subscribe(data, request, session):
    fu = asyncio.Future()
    async def check_identity():
        sess = await get_session(request)
        if not sess.get('uid'):
            fu.set_exception(InvalidRequest("Login required"))
            return False
        if not await request.app.models.user.is_administrator(sess['uid']):
            fu.set_exception(InvalidRequest("Permission denied"))
            return False
        return True
    async def send_add(user_parameter):
        if await check_identity():
            session.send({user_parameter['id']: "add"})
    async def send_update(user_parameter):
        if await check_identity():
            session.send({user_parameter['id']: "update"})
    async def send_remove(user_parameter):
        if await check_identity():
            session.send({user_parameter['id']: "remove"})
    request.app.models.event.add_event_listener("user-add", send_add)
    request.app.models.event.add_event_listener("user-remove", send_remove)
    request.app.models.event.add_event_listener("user-update", send_update)
    await check_identity()
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener("user-add", send_add)
        request.app.models.event.remove_event_listener("user-remove", send_remove)
        request.app.models.event.remove_event_listener("user-update", send_update)

handlers = {
    'user-add': (user_add, ('ajax-post', 'ws')),
    'user-info': (user_info, ('ajax-get', 'ws')),
    'user-get-id': (user_get_id, ('ajax-get', 'ws')),
    'user-remove': (user_remove, ('ajax-delete', 'ws')),
    'login': (login, ('ajax-post', 'ws')),
    'logout': (logout, ('ajax-get', 'ws')),
    'check-session': (check_session, ('ajax-get', 'ws')),
    'user-list': (user_list, ('ajax-get', 'ws')),
    'user-get-settings': (user_get_settings, ('ajax-get',)),
    'user-set-settings': (user_set_settings, ('ajax-post',)),
    'user-set-role': (user_set_role, ('ajax-post', 'ws')),
    'user-update': (user_update, ('ajax-post',)),
    'user-set-password': (user_set_password, ('ajax-post',)),
    'user-info-subscribe': (user_info_subscribe, ('ws',)),
    'user-list-subscribe': (user_list_subscribe, ('ws',)),
}
