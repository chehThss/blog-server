from typing import List, Tuple, Callable
from .websocket import websocket_handler
from .ajax import ajax_handler

routes: List[Tuple[str, str, Callable, str]] = [
    ('GET', '/ws', websocket_handler, 'ws'),
    ('GET', '/api/{action}', ajax_handler, 'ajax-get'),
    ('POST', '/api/{action}', ajax_handler, 'ajax-post'),
    ('PUT', '/api/{action}', ajax_handler, 'ajax-put'),
    ('DELETE', '/api/{action}', ajax_handler, 'ajax-delete'),
    ('PATCH', '/api/{action}', ajax_handler, 'ajax-patch'),
    ('OPTIONS', '/api/{action}', ajax_handler, 'ajax-options'),
]
