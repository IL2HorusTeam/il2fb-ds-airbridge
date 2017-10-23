# coding: utf-8

import asyncio

from typing import Awaitable

import janus

from il2fb.commons.events import Event
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.console.events import ChatMessageWasReceived
from il2fb.parsers.game_log import events as game_log_events

from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker
from il2fb.ds.airbridge.structures import TimestampedData
from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


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

        self._subscribers = []
        self._subscribers_lock = asyncio.Lock(loop=loop)

    async def subscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                self._console_client.subscribe_to_chat(
                    subscriber=self._consume,
                )
            self._subscribers.append(subscriber)

    async def unsubscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                self._console_client.unsubscribe_from_chat(
                    subscriber=self._consume,
                )

    def _consume(self, event: ChatMessageWasReceived) -> None:
        item = TimestampedData(event)
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


class EventsStreamingFacility:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        console_client: ConsoleClient,
        game_log_worker: GameLogWorker,
    ):
        self._loop = loop
        self._console_client = console_client
        self._game_log_worker = game_log_worker

        self._queue = janus.Queue(loop=loop)
        self._queue_task = None

        self._subscribers = []
        self._subscribers_lock = asyncio.Lock(loop=loop)


    async def subscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                self._console_client.subscribe_to_human_connection_events(
                    subscriber=self._consume_human_connection_event,
                )
                self._game_log_worker.subscribe_to_events(
                    subscriber=self._consume_game_log_event,
                )
            self._subscribers.append(subscriber)

    async def unsubscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                self._console_client.unsubscribe_from_human_connection_events(
                    subscriber=self._consume_human_connection_event,
                )
                self._game_log_worker.unsubscribe_from_events(
                    subscriber=self._consume_game_log_event,
                )

    def _consume_human_connection_event(self, event: Event) -> None:
        item = TimestampedData(event)
        self._queue.async_q.put_nowait(item)

    def _consume_game_log_event(self, event: Event) -> None:
        ignored_events = (
            game_log_events.HumanHasConnected,
            game_log_events.HumanHasDisconnected,
        )
        if isinstance(event, ignored_events):
            return

        item = TimestampedData(event)
        self._queue.sync_q.put_nowait(item)

    def start(self):
        coroutine = self._process_queue()
        self._queue_task = self._loop.create_task(coroutine)

    async def _process_queue(self):
        while True:
            item = await self._queue.async_q.get()
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
                            f"subscriber failed to handle game event "
                            f"(item={repr(item)})"
                        )

    def stop(self):
        if self._queue_task:
            self._queue.async_q.put_nowait(None)

    async def wait_stopped(self) -> Awaitable[None]:
        if self._queue_task:
            await self._queue_task


class NotParsedStringsStreamingFacility:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        game_log_worker: GameLogWorker,
    ):
        self._loop = loop
        self._game_log_worker = game_log_worker

        self._queue = janus.Queue(loop=loop)
        self._queue_task = None

        self._subscribers = []
        self._subscribers_lock = asyncio.Lock(loop=loop)

    async def subscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                self._game_log_worker.subscribe_to_not_parsed_strings(
                    subscriber=self._consume,
                )
            self._subscribers.append(subscriber)

    async def unsubscribe(
        self,
        subscriber: StreamingSubscriber,
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                self._game_log_worker.unsubscribe_from_not_parsed_strings(
                    subscriber=self._consume,
                )

    def _consume(self, s: str) -> None:
        item = TimestampedData(s)
        self._queue.sync_q.put_nowait(item)

    def start(self):
        coroutine = self._process_queue()
        self._queue_task = self._loop.create_task(coroutine)

    async def _process_queue(self):
        while True:
            item = await self._queue.async_q.get()
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
                            f"subscriber failed to handle not parsed string "
                            f"(item={repr(item)})"
                        )

    def stop(self):
        if self._queue_task:
            self._queue.async_q.put_nowait(None)

    async def wait_stopped(self) -> Awaitable[None]:
        if self._queue_task:
            await self._queue_task
