from typing import Dict, Tuple, Set, Callable
from .examples import handlers as examples_handlers
from .session import Session
from .exception import InvalidRequest

async def api_list():
    result = {}
    for n, (h, p) in handlers.items():
        result[n] = list(p)
    return result

handlers: Dict[str, Tuple[Callable, Set[str]]] = {
    'api-list': (api_list, {'ajax-get', 'ws'})
}

handlers.update(examples_handlers)
