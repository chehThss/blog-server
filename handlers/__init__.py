from typing import Dict, Tuple, Callable
from .session import Session
from .exception import InvalidRequest
from .examples import handlers as examples_handlers
from .user import handlers as user_handlers
from .file import handlers as file_handlers
from .post import handlers as post_handlers
from .settings import handlers as settings_handlers
from .post_categories import handlers as post_categories_handlers

async def api_list():
    result = {}
    for n, (h, p) in handlers.items():
        result[n] = p
    return result

handlers: Dict[str, Tuple[Callable, Tuple[str]]] = {
    'api-list': (api_list, ('ajax-get', 'ws'))
}

handlers.update(examples_handlers)
handlers.update(user_handlers)
handlers.update(file_handlers)
handlers.update(post_handlers)
handlers.update(settings_handlers)
handlers.update(post_categories_handlers)
