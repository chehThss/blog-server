from aiohttp import web

async def allow_origin(app, handler):
    async def middleware(request):
        if request.method == web.hdrs.METH_OPTIONS:
            response = web.Response()
        else:
            response = await handler(request)
        response.headers.add("Access-Control-Allow-Origin", request.headers.get('origin') or 'http://localhost')
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,X-Requested-With,Cache-Control")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        return response
    return middleware
