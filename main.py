import asyncio
import json
from aiohttp_session import session_middleware
from aiohttp_session.redis_storage import RedisStorage
import aioredis
from aiohttp import web
from motor import motor_asyncio
from routes import routes
from models import Models
from middlewares import middlewares
from os.path import isdir


class App:
    def __init__(self, config):
        self.config = config
        self.app = None
        self.redis_pool = None
        self.db_client = None
        self.handler = None
        self.server = None

    async def startup(self):
        self.app = web.Application()
        self.app.config = self.config
        self.redis_pool = await aioredis.create_pool(('localhost', 6379))
        self.app.middlewares.extend([
            session_middleware(RedisStorage(self.redis_pool)),
            *middlewares
        ])
        for route in routes:
            self.app.router.add_route(*route[:3], name=route[3])
        self.app.models = Models(self.config)
        await self.app.models.startup()
        self.app.websockets = []
        async def on_shutdown(_app):
            for ws in _app.websockets:
                await ws.shutdown()
        self.app.on_shutdown.append(on_shutdown)
        _loop = asyncio.get_event_loop()
        self.handler = self.app.make_handler(loop=_loop)
        self.server = await _loop.create_server(self.handler, self.config['host'], self.config['port'])

    async def shutdown(self):
        self.server.close()
        self.redis_pool.close()
        await self.shutdown()
        await self.server.wait_closed()
        await self.redis_pool.wait_closed()
        await self.app.shutdown()
        await self.handler.shutdown(60.0)
        await self.app.cleanup()

if __name__ == '__main__':
    with open('config.json') as f:
        global_config = json.load(f)
    if not isdir(global_config['upload-path']):
        raise RuntimeError('Upload path does not exist')
    app = App(global_config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.startup())
    print('serving on http://%s:%d' % app.server.sockets[0].getsockname())
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('stopping server')
        loop.run_until_complete(app.shutdown())
    loop.close()
