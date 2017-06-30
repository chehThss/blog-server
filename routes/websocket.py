import asyncio
import json
from typing import Dict, Callable, Any, Coroutine, Tuple
from aiohttp import web, WSMsgType, WSCloseCode
from inspect import signature

handlers: Dict[str, Callable[[Any, Any], Coroutine[Any, Any, Any]]] = {

}


class InvalidRequest(Exception):
    pass


class Session:
    def __init__(self, ws: web.WebSocketResponse, sid: str):
        self._ws = ws
        self._id = sid
        self._queue = asyncio.Queue()
        self._finished = False
        self._default_timeout = None

    @property
    def id(self):
        return self._id

    @property
    def finished(self):
        return self._finished

    def close(self):
        self.finished = True

    @finished.setter
    def finished(self, value: bool):
        self._finished = value

    @property
    def default_timeout(self):
        return self._default_timeout

    @default_timeout.setter
    def default_timeout(self, value):
        self._default_timeout = value

    def send(self, data=None, status=None):
        # If finished, just ignored the data. Warning may be better
        if self.finished:
            return
        finished = status is not None
        self._ws.send_str(json.dumps({
            'id': self._id,
            'action': '$finish' if finished else '$resume',
            **({'status': status} if finished else {}),
            **({'data': data} if data else {}),
        }, ensure_ascii=False))
        if finished:
            self.finished = True

    async def recv(self, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        if not self.finished:
            result = asyncio.ensure_future(asyncio.wait_for(self._queue.get(), timeout=timeout))
        elif self.has_recv():
            result = self._queue.get_nowait()
        else:
            raise asyncio.CancelledError()
        return result

    async def feed(self, data=None, status=None):
        # If finished, just ignored the data. Warning may be better
        if self.finished:
            return
        await self._queue.put((data, status))
        if status is not None:
            self.finished = True

    def has_recv(self):
        return not self._queue.empty()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.finished and not self.has_recv():
            raise StopAsyncIteration
        return await self.recv()


class Client:
    def __init__(self, request: web.Request):
        self.request = request
        self.sessions: Dict[str, Tuple[Any, Session]] = {}

    async def startup(self):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(self.request)
        return self.ws

    async def run(self):
        async for msg in self.ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if (type(data) is not dict or 'id' not in data or type(data['id']) is not str or
                            'action' not in data or type(data['action'] is not str)):
                        await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
                    else:
                        if data['action'] == '$resume' or data['action'] == '$finish':
                            if data['id'] not in self.sessions:
                                Session(self.ws, data['id']).send('Invalid session')
                            await self.sessions[data['id']][1].feed(data)
                        if not data['action'] in handlers:
                            raise InvalidRequest('Unsupported action')
                        result = await handlers[data['action']](data.get('data'))
                        self.ws.send_str(json.dumps({
                            'id': data['id'],
                            'action': '$finished',
                            'status': 0,
                            ** ({'data': result} if result is not None else {})
                        }, ensure_ascii=False))
                except json.JSONDecodeError:
                    await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
            elif msg.type == WSMsgType.TEXT:
                await self.shutdown(WSCloseCode.UNSUPPORTED_DATA, message='Support only text data')

    async def handler_wrapper(self, sid: str, handler, data, request):
        async def run_handler():
            try:
                result = await handler(*(data, request, sessions)[:len(signature(handler).parameters)])
                if not session.finished:
                    session.send(result, status=0)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError as err:
                if not session.finished:
                    session.send(str(err), status=1)
            except InvalidRequest as err:
                if not session.finished:
                    session.send(str(err), status=1)
            except:
                if not session.finished:
                    session.send('Server internal error', status=2)
            finally:
                del self.sessions[session.id]

    async def shutdown(self, code=WSCloseCode.GOING_AWAY, message='Server shutdown'):
        for s in self.sessions.values():
                s.cancel()
        return await self.ws.close(code=code, message=message)

async def websocket_handler(request):
    client = Client(request)
    ws = await client.startup()
    request.app.websockets.append(client)
    try:
        await client.run()
    finally:
        request.app.websockets.remove(client)
    return ws
