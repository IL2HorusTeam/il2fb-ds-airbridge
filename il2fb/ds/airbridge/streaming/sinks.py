# coding: utf-8

import abc
import asyncio

from typing import Any, Awaitable, List


class StreamingSink(metaclass=abc.ABCMeta):

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


class JointStreamingSink(StreamingSink, list):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        items: List[StreamingSink],
    ):
        self._loop = loop
        super().__init__(items)

    async def write(self, o: Any) -> Awaitable[None]:
        if self:
            awaitables = [item.write(o) for item in self]
            await asyncio.gather(*awaitables, loop=self._loop)

    def open(self) -> None:
        for item in self:
            item.open()

    async def wait_opened(self) -> Awaitable[None]:
        if self:
            awaitables = [item.wait_opened() for item in self]
            await asyncio.gather(*awaitables, loop=self._loop)

    def close(self) -> None:
        for item in self:
            item.close()

    async def wait_closed(self) -> Awaitable[None]:
        if self:
            awaitables = [item.wait_closed() for item in self]
            await asyncio.gather(*awaitables, loop=self._loop)
