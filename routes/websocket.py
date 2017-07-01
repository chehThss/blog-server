import asyncio
import json
from inspect import signature
from typing import Dict, Tuple, Callable, Any
from aiohttp import web, WSMsgType, WSCloseCode
from . import handlers

global_handlers: Dict[str, Callable] = {}
for n, (h, p) in handlers.handlers.items():
    if 'ws' in p:
        global_handlers[n] = h


class Session:
    def __init__(self, ws: web.WebSocketResponse, sid: str):
        self._ws = ws
        self._id = sid
        self._queue = asyncio.Queue()
        self.finished = False
        self.default_timeout = None

    @property
    def id(self):
        return self._id

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
            result = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        elif self.has_recv():
            result = self._queue.get_nowait()
        else:
            raise RuntimeError('recv called with finished session')
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
        self.ws = web.WebSocketResponse()

    async def startup(self):
        await self.ws.prepare(self.request)
        return self.ws

    async def run(self):
        async for msg in self.ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if type(data) is not dict or 'id' not in data or type(data['id']) is not str or \
                            'action' not in data or type(data['action'] is not str) or \
                            (data['action'] == '$finish' and ('status' not in data or type(data['status']) is not int)):
                        await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
                    elif data['action'] == '$resume' or data['action'] == '$finish':
                        if data['id'] not in self.sessions:
                            Session(self.ws, data['id']).send('Unknown session', status=1)
                        status = None if data['action'] == '$resume' else data['status']
                        await self.sessions[data['id']][1].feed(data.get('data'), status)
                    elif data['id'] in self.sessions:
                        Session(self.ws, data['id']).send('Conflicting session', status=1)
                        self.sessions[data['id']][0].cancel()
                    elif not data['action'] in handlers:
                        Session(self.ws, data['id']).send('Unknown action', status=1)
                    else:
                        session = Session(self.ws, data['id'])
                        future = asyncio.ensure_future(self.handler_wrapper(
                            global_handlers[data['action']], data.get('data'), session))
                        self.sessions[data['id']] = future, session

                        def future_done_callback(fu):
                            del self.sessions[data['id']]
                        future.add_done_callback(future_done_callback)

                except json.JSONDecodeError:
                    await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
            elif msg.type == WSMsgType.BINARY:
                await self.shutdown(WSCloseCode.UNSUPPORTED_DATA, message='Support only text data')

    async def handler_wrapper(self, handler, data, session: Session):
        try:
            result = await handler(*(data, self.request, session)[:len(signature(handler).parameters)])
            if not session.finished:
                session.send(result, status=0)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError as err:
            if not session.finished:
                session.send(str(err), status=1)
        except handlers.InvalidRequest as err:
            if not session.finished:
                session.send(str(err), status=1)
        except:
            if not session.finished:
                session.send('Server internal error', status=2)
        finally:
            del self.sessions[session.id]

    async def shutdown(self, code=WSCloseCode.GOING_AWAY, message='Server shutdown'):
        for f, s in self.sessions.values():
                f.cancel()
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
