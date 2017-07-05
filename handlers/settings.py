from models import Settings

# settings_set
async def settings_get(data, request):
    settings: Settings = request.app.models.settings
    return await settings.get()

async def settings_set(data, request):
    settings: Settings = request.app.models.settings
    return await settings.set(data)

handlers = {
    'settings-get': (settings_get, ('ajax-get',)),
    'settings-set': (settings_set, ('ajax-post',)),
}