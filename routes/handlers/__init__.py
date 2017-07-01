from typing import Dict, Tuple, Set, Callable
from .exception import InvalidRequest

async def api_list():
    result = {}
    for n, (h, p) in handlers.items():
        result[n] = list(p)
    return result

handlers: Dict[str, Tuple[Callable, Set[str]]] = {
    'api-list': (api_list, {'ajax-get', 'ajax-post', 'ws'})
}
