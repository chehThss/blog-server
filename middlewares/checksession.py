from models import User
from aiohttp_session import get_session
from handlers.exception import InvalidRequest

async def check_session(app, handler):
    async def middleware(request):
        session = await get_session(request)
        if 'uid' in session:
            user: User = request.app.models.user
            try:
                await user.info(session['uid'], {'_id': True})
            except InvalidRequest:
                del session['uid']
        return await handler(request)
    return middleware
