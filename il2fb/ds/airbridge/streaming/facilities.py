# coding: utf-8

import abc
import asyncio
import logging

from typing import Awaitable, Optional

import janus

from il2fb.commons.events import Event
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.console.events import ChatMessageWasReceived
from il2fb.parsers.game_log import events as game_log_events

from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker
from il2fb.ds.airbridge.structures import TimestampedData
from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


LOG = logging.getLogger(__name__)


class StreamingFacility(metaclass=abc.ABCMeta):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        queue: Optional[asyncio.Queue]=None,
    ):
        self._loop = loop
        self._name = name

        self._queue = queue or asyncio.Queue(loop=loop)
        self._queue_task = None

        self._subscribers = []
        self._subscribers_lock = asyncio.Lock(loop=loop)

    async def subscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                await self._before_first_subscriber()
            self._subscribers.append(subscriber)

    async def _before_first_subscriber(self) -> Awaitable[None]:
        pass

    async def unsubscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                await self._after_last_subscriber()

    async def _after_last_subscriber(self) -> Awaitable[None]:
        pass

    def start(self) -> None:
        coroutine = self._process_queue()
        self._queue_task = self._loop.create_task(coroutine)

    async def _process_queue(self) -> Awaitable[None]:
        LOG.info(f"streaming facility '{self._name}' was started")

        while True:
            item = await self._queue.get()
            if item is None:
                break

            with await self._subscribers_lock:
                if not self._subscribers:
                    continue

                try:
                    awaitables = [
                        subscriber(item)
                        for subscriber in self._subscribers
                    ]
                    await asyncio.gather(*awaitables, loop=self._loop)
                except:
                    LOG.exception(
                        f"failed to handle streaming item "
                        f"(facility='{self._name}', item={repr(item)})"
                    )

        LOG.info(f"streaming facility '{self._name}' was stopped")

    def stop(self) -> None:
        if self._queue_task:
            self._queue.put_nowait(None)

    async def wait_stopped(self) -> Awaitable[None]:
        if self._queue_task:
            await self._queue_task


class ChatStreamingFacility(StreamingFacility):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        console_client: ConsoleClient,
        name: str="chat",
    ):
        self._console_client = console_client
        super().__init__(loop=loop, name=name)

    async def _before_first_subscriber(self) -> Awaitable[None]:
        self._console_client.subscribe_to_chat(subscriber=self._consume)

    async def _after_last_subscriber(self) -> Awaitable[None]:
        self._console_client.unsubscribe_from_chat(subscriber=self._consume)

    def _consume(self, event: ChatMessageWasReceived) -> None:
        item = TimestampedData(event)
        self._queue.put_nowait(item)


class EventsStreamingFacility(StreamingFacility):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        console_client: ConsoleClient,
        game_log_worker: GameLogWorker,
        name: str="events",
    ):
        self._console_client = console_client
        self._game_log_worker = game_log_worker

        queue = janus.Queue(loop=loop)
        self._queue_thread_safe = queue.sync_q

        super().__init__(loop=loop, name=name, queue=queue.async_q)

    async def _before_first_subscriber(self) -> Awaitable[None]:
        self._game_log_worker.subscribe_to_events(
            subscriber=self._consume_game_log_event,
        )
        self._console_client.subscribe_to_human_connection_events(
            subscriber=self._consume_human_connection_event,
        )

    async def _after_last_subscriber(self) -> Awaitable[None]:
        self._console_client.unsubscribe_from_human_connection_events(
            subscriber=self._consume_human_connection_event,
        )
        self._game_log_worker.unsubscribe_from_events(
            subscriber=self._consume_game_log_event,
        )

    def _consume_human_connection_event(self, event: Event) -> None:
        item = TimestampedData(event)
        self._queue.put_nowait(item)

    def _consume_game_log_event(self, event: Event) -> None:
        ignored_events = (
            game_log_events.HumanHasConnected,
            game_log_events.HumanHasDisconnected,
        )
        if isinstance(event, ignored_events):
            return

        item = TimestampedData(event)
        self._queue_thread_safe.put_nowait(item)


class NotParsedStringsStreamingFacility(StreamingFacility):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        game_log_worker: GameLogWorker,
        name: str="not_parsed_strings",
    ):
        self._game_log_worker = game_log_worker

        queue = janus.Queue(loop=loop)
        self._queue_thread_safe = queue.sync_q

        super().__init__(loop=loop, name=name, queue=queue.async_q)

    async def _before_first_subscriber(self) -> Awaitable[None]:
        self._game_log_worker.subscribe_to_not_parsed_strings(
            subscriber=self._consume,
        )

    async def _after_last_subscriber(self) -> Awaitable[None]:
        self._game_log_worker.unsubscribe_from_not_parsed_strings(
            subscriber=self._consume,
        )

    def _consume(self, s: str) -> None:
        item = TimestampedData(s)
        self._queue.put_nowait(item)
