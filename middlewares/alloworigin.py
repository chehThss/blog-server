from motor import motor_asyncio
from handlers.exception import InvalidRequest
from bson import ObjectId


async def allow_origin(app, handler):
    async def middleware(request):
        response = await handler(request)
        response.headers.add("Access-Control-Allow-Origin", request.headers.get('origin') or 'http://localhost')
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        return response
    return middleware
