from .alloworigin import allow_origin
from .checksession import check_session

middlewares = [
    allow_origin,
    check_session
]

