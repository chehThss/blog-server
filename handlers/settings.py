from models import Settings

# settings_set
async def settings_get(data, request):
    pass


handlers = {
    'settings-get': (settings_get, ('ajax-get',)),
}