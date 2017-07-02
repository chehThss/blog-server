import asyncio
import json
import traceback
from inspect import signature
from typing import Dict, Tuple, Callable, Any
from aiohttp import web, WSMsgType, WSCloseCode
from handlers import handlers, InvalidRequest, Session

global_handlers: Dict[str, Callable] = {}
for n, (h, p) in handlers.items():
    if 'ws' in p:
        global_handlers[n] = h


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
                    if not isinstance(data, dict) or 'id' not in data or not isinstance(data['id'], str)or \
                            'action' not in data or not isinstance(data['action'], str) or \
                            (data['action'] == '$finish' and
                             ('status' not in data or not isinstance(data['status'], int))):
                        await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
                    elif data['action'] == '$resume' or data['action'] == '$finish':
                        if data['id'] not in self.sessions:
                            Session(self.ws, data['id']).send('Unknown session', status=1)
                        else:
                            status = None if data['action'] == '$resume' else data['status']
                            await self.sessions[data['id']][1].feed(data.get('data'), status)
                            if status is not None:
                                self.sessions[data['id']][0].cancel()
                    elif data['id'] in self.sessions:
                        Session(self.ws, data['id']).send('Conflicting session', status=1)
                    elif data['action'] not in global_handlers:
                        Session(self.ws, data['id']).send('Unknown action', status=1)
                    else:
                        sid = data['id']
                        session = Session(self.ws, sid)
                        future = asyncio.ensure_future(self.handler_wrapper(
                            global_handlers[data['action']], data.get('data'), session))
                        self.sessions[sid] = future, session

                        def future_done_callback(key):
                            def _callback(fu):
                                del self.sessions[key]
                            return _callback
                        future.add_done_callback(future_done_callback(sid))
                except json.JSONDecodeError:
                    await self.shutdown(WSCloseCode.INVALID_TEXT, message='Invalid request')
            elif msg.type == WSMsgType.BINARY:
                await self.shutdown(WSCloseCode.UNSUPPORTED_DATA, message='Support only text data')
        for f, s in self.sessions.values():
            f.cancel()

    async def handler_wrapper(self, handler, data, session: Session):
        try:
            result = await handler(*(data, self.request, session)[:len(signature(handler).parameters)])
            if isinstance(result, BaseException):
                raise result
            if not session.finished:
                session.send(result, status=0)
        except asyncio.CancelledError:
            raise
        except (InvalidRequest, web.HTTPClientError) as err:
            if not session.finished:
                session.send(str(err), status=1)
        except:
            if not session.finished:
                session.send('Server internal error', status=2)
            traceback.print_exc()
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
