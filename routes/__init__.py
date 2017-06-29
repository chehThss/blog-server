from .websocket import websocket_handler

routes = [
    ('GET', '/ws', websocket_handler),
]