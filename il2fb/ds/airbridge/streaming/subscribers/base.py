# coding: utf-8

import abc

from typing import Any, Awaitable


class StreamingSubscriber(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def write(self, o: Any) -> Awaitable[None]:
        pass


class PluggableStreamingSubscriber(StreamingSubscriber):

    def __init__(self, app):
        self._app = app

    def plug_in(self) -> None:
        pass

    async def wait_plugged(self) -> Awaitable[None]:
        pass

    def unplug(self) -> None:
        pass

    async def wait_unplugged(self) -> Awaitable[None]:
        pass
