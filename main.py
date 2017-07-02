import asyncio
import json
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp import web
from motor import motor_asyncio
from routes import routes
from models import Models
from middlewares import middlewares

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)

    app = web.Application()
    app.middlewares.extend([
        session_middleware(EncryptedCookieStorage(config['secret-key'])),
        *middlewares
    ])
    client = motor_asyncio.AsyncIOMotorClient(config['db'])
    app.models = Models(client.get_default_database())
    app.websockets = []
    async def on_shutdown(_app):
        for ws in _app.websockets:
            await ws.shutdown()
    for route in routes:
        app.router.add_route(*route[:3], name=route[3])
    app.on_shutdown.append(on_shutdown)

    loop = asyncio.get_event_loop()
    handler = app.make_handler(loop=loop)
    srv = loop.run_until_complete(loop.create_server(handler, config['host'], config['port']))
    print('serving on http://%s:%d' % srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('stopping server')
        srv.close()
        client.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.shutdown())
        loop.run_until_complete(handler.shutdown(60.0))
        loop.run_until_complete(app.cleanup())
    loop.close()
