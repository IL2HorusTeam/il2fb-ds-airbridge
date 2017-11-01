# coding: utf-8

import abc

from typing import Any, Awaitable


class StreamingSubscriber(metaclass=abc.ABCMeta):

    def __init__(self, app):
        self._app = app

    @abc.abstractmethod
    async def write(self, o: Any) -> Awaitable[None]:
        pass

    def open(self) -> None:
        pass

    async def wait_opened(self) -> Awaitable[None]:
        pass

    def close(self) -> None:
        pass

    async def wait_closed(self) -> Awaitable[None]:
        pass
