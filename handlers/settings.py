from models import Settings, User
from aiohttp_session import get_session
from .exception import InvalidRequest


async def settings_get(data, request):
    settings: Settings = request.app.models.settings
    return await settings.get()

async def settings_set(data, request):
    settings: Settings = request.app.models.settings
    user: User = request.app.models.user
    session = await get_session(request)
    if 'uid' not in session or not (await user.is_administrator(session['uid'])):
        raise InvalidRequest('Permission denied')
    return await settings.set(data)

handlers = {
    'settings-get': (settings_get, ('ajax-get',)),
    'settings-set': (settings_set, ('ajax-post',)),
}
