from typing import List, Tuple, Callable
from .websocket import websocket_handler
from .ajax import ajax_get

routes: List[Tuple[str, str, Callable, str]] = [
    ('GET', '/ws', websocket_handler, 'ws'),
    ('GET', '/api/{action}', ajax_get, 'ajax-get')
]
