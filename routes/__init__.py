from typing import List, Tuple, Callable
from .websocket import websocket_handler
from .ajax import ajax_handler
from .file import file_handler

routes: List[Tuple[str, str, Callable, str]] = [
    ('GET', '/ws', websocket_handler, 'ws'),
    ('*', '/api/{action}', ajax_handler, 'ajax'),
    ('*', r'/file{path:/.*}', file_handler, 'file')
]
