from aiohttp_session import get_session
from time import time
from handlers.exception import InvalidRequest

ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'

def set_session(session, user_id):
    session['user'] = str(user_id)
    session['last_visit'] = time()

async def user_add(data, request):
    user = request.app.models.user
    # TODO: check input
    return await user.add(data['username'], data['password'], ROLE_EDITOR)

async def user_info(data, request):
    user = request.app.models.user
    # TODO: check input
    return await user.info(data['id'])

async def user_remove(data, request):
    user = request.app.models.user
    # TODO: check input
    return await user.remove(data)

async def user_login(data, request):
    user = request.app.models.user
    # TODO: check input
    user_id = await user.check_user(data['username'], data['password'])
    session = await get_session(request)
    set_session(session, user_id)
    # TODO: redirect

async def check_session(request):
    session = await get_session(request)
    if 'user' in session:
        return "success"
        #TODO: redirect

async def user_signout(request):
    session = await get_session(request)
    if 'user' in session:
        del session['user']
        # TODO: redirect
    else:
        raise InvalidRequest("User already signs out")

handlers = {
    'user-add': (user_add, {'ajax-post', 'ws'}),
    'user-info': (user_info, {'ajax-get', 'ws'}),
    'user-remove': (user_remove, {'ajax-delete', 'ws'}),
    'user-login': (user_login, {'ajax-post', 'ws'}),
    'check-session': (check_session, {'ajax-get', 'ws'}),
    'user-signout': (user_signout, {'ajax-get', 'ws'}),
}
