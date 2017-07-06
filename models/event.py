from typing import Callable, Dict, List
import asyncio


class Event:
    def __init__(self):
        self.events: Dict[str, List[Callable]] = dict()

    def on(self, name: str, handler: Callable):
        handlers = self.events.get(name)
        if handlers is None:
            self.events[name] = [handler]
        else:
            self.events[name].append(handler)
        return handler

    def emit(self, name, *args, **kwargs):
        if name in self.events:
            for handler in self.events[name]:
                asyncio.ensure_future(handler(*args, **kwargs))

    def add_event_listener(self, name: str, handler: Callable):
        self.on(name, handler)

    def remove_event_listener(self, name: str, handler: Callable):
        if handler in self.events[name]:
            self.events[name].remove(handler)
