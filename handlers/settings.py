from models import Settings, User
from aiohttp_session import get_session
from .exception import InvalidRequest
import asyncio


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

async def settings_subscribe(data, request, session):
    fu = asyncio.Future()
    async def send_settings(settings_parameter):
        session.send({settings_parameter['key']: settings_parameter['value']})
    request.app.models.event.add_event_listener('settings-update', send_settings)
    try:
        await fu
    finally:
        request.app.models.event.remove_event_listener('settings-update', send_settings)

handlers = {
    'settings-get': (settings_get, ('ajax-get',)),
    'settings-set': (settings_set, ('ajax-post',)),
    'settings-subscribe': (settings_subscribe, ('ws',)),
}
