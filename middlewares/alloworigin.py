from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId


async def allow_origin(app, handler):
    async def middleware(request):
        response = await handler(request)
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "X-Requested-With")
        return response
    return middleware
