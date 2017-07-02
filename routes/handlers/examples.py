import asyncio
from .exception import InvalidRequest

async def hello():
    return "hello"

async def echo(data, request, session):
    # Returns all the data its received
    if session:
        # It's a WebSocket connection
        session.send(data)
        session.default_timeout = 10 # Timeout for `await` or `async for`, default is None(No timeout)
        try:
            async for data, status in session:
                # Stop iteration when client fired a `$finish` action
                # or 10s has passed without any message
                session.send(data)
        except asyncio.TimeoutError:
            raise InvalidRequest('Timeout')
    else:
        return data

async def subscribe(data, request, session):
    # Simulates a event emitter that notifies the client every `data` (in seconds) interval
    # Finished when the client emits a `$finish` action, or counter reaches 10
    if not isinstance(data, int) and not isinstance(data, float):
        raise InvalidRequest('Invalid Request')
    count = 0
    while count < 10:
        count += 1
        session.send(count)
        # You can also manually fire a `$finish` action, just like the following statement. Notice that if you do this,
        #           the final message will also carry a data, which is different from the origin one
        #session.send(count, 0 if count == 10 else None)
        await asyncio.sleep(data)

handlers = {
    'hello': (hello, {'ajax-get', 'ws'}),
    'echo': (echo, {'ajax-get', 'ajax-post', 'ajax-put', 'ajax-delete', 'ajax-patch', 'ws'}), # Supports all protocol
    'subscribe': (subscribe, 'ws')
}
