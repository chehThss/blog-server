from typing import Dict, Tuple, Set, Callable
from .session import Session
from .exception import InvalidRequest
from .examples import handlers as examples_handlers
from .user import handlers as user_handlers

async def api_list():
    result = {}
    for n, (h, p) in handlers.items():
        result[n] = list(p)
    return result

handlers: Dict[str, Tuple[Callable, Set[str]]] = {
    'api-list': (api_list, {'ajax-get', 'ws'})
}

handlers.update(examples_handlers)
handlers.update(user_handlers)
