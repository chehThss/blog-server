ROLE_ADMIN = 'administrator'
ROLE_EDITOR = 'editor'

async def user_add(data, request):
    user = request.app.models.user
    # TODO: check input
    return user.add(data['username'], user['password'], ROLE_EDITOR)


