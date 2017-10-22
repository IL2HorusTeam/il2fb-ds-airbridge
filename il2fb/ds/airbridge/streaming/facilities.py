# coding: utf-8

import asyncio

from typing import Awaitable

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.console.events import ChatMessageWasReceived

from il2fb.ds.airbridge.structures import TimestampedItem
from il2fb.ds.airbridge.typing import AsyncTimestampedItemHandler


class ChatStreamingFacility:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        console_client: ConsoleClient,
    ):
        self._loop = loop
        self._console_client = console_client

        self._queue = asyncio.Queue(loop=loop)
        self._queue_task = None

        self._subscribers_lock = asyncio.Lock(loop=loop)
        self._subscribers = []

    async def subscribe(
        self,
        subscriber: AsyncTimestampedItemHandler,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                self._console_client.subscribe_to_chat(
                    subscriber=self._consume,
                )
            self._subscribers.append(subscriber)

    async def unsubscribe(
        self,
        subscriber: AsyncTimestampedItemHandler,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                self._console_client.unsubscribe_from_chat(
                    subscriber=self._consume,
                )

    def _consume(self, event: ChatMessageWasReceived) -> None:
        item = TimestampedItem(event)
        self._queue.put_nowait(item)

    def start(self):
        coroutine = self._process_queue()
        self._queue_task = self._loop.create_task(coroutine)

    async def _process_queue(self):
        while True:
            item = await self._queue.get()
            if item is None:
                break

            with await self._subscribers_lock:
                for subscriber in self._subscribers:
                    try:
                        result = subscriber(item)
                        if asyncio.iscoroutine(result):
                            await result
                    except:
                        LOG.exception(
                            f"subscriber failed to handle chat event "
                            f"(item={repr(item)})"
                        )

    def stop(self):
        if self._queue_task:
            self._queue.put_nowait(None)

    async def wait_stopped(self) -> Awaitable[None]:
        if self._queue_task:
            await self._queue_task
