ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'

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
    return await user.login(data['username'], data['password'])

async def user_signout(data, request):
    user = request.app.models.user
    # TODO: check input
    return await user.signout(data['id'])

handlers = {
    'user-add': (user_add, {'ajax-post', 'ws'}),
    'user-info': (user_info, {'ajax-get', 'ws'}),
    'user-remove': (user_remove, {'ajax-delete', 'ws'}),
    'user-login': (user_login, {'ajax-post', 'ws'}),
    'user-signout': (user_signout, {'ajax-post', 'ws'}),
}
