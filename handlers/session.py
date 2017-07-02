from aiohttp import web
import asyncio
import json


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
