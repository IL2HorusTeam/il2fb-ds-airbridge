# coding: utf-8

import abc
import asyncio
import functools
import logging
import math
import time

from concurrent.futures import CancelledError
from typing import Awaitable, Optional

import janus

from il2fb.commons.events import Event

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.console.events import ChatMessageWasReceived

from il2fb.parsers.game_log import events as game_log_events

from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker
from il2fb.ds.airbridge.dedicated_server.game_log import NotParsedGameLogString
from il2fb.ds.airbridge.radar import Radar
from il2fb.ds.airbridge.structures import TimestampedData
from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


LOG = logging.getLogger(__name__)


class StreamingFacility(metaclass=abc.ABCMeta):

    def __init__(self, loop: asyncio.AbstractEventLoop, name: str):
        self._loop = loop
        self._name = name
        self._main_task = None

    @abc.abstractmethod
    async def subscribe(self, subscriber: StreamingSubscriber, **kwargs) -> Awaitable[None]:
        pass

    @abc.abstractmethod
    async def unsubscribe(self, subscriber: StreamingSubscriber) -> Awaitable[None]:
        pass

    def start(self) -> None:
        coroutine = self._try_run()
        self._main_task = asyncio.ensure_future(coroutine, loop=self._loop)

    async def _try_run(self) -> Awaitable[None]:
        try:
            LOG.info(
                f"streaming facility '{self._name}': started"
            )
            await self._run()
        except Exception:
            LOG.exception(
                f"streaming facility '{self._name}': terminated"
            )
        else:
            LOG.info(
                f"streaming facility '{self._name}': stopped"
            )

    @abc.abstractmethod
    async def _run(self) -> Awaitable[None]:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass

    async def wait_stopped(self) -> Awaitable[None]:
        if self._main_task:
            await self._main_task


class QueueStreamingFacility(StreamingFacility):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        queue: Optional[asyncio.Queue]=None,
    ):
        super().__init__(loop=loop, name=name)

        self._queue = queue or asyncio.Queue(loop=loop)

        self._subscribers = []
        self._subscribers_lock = asyncio.Lock(loop=loop)

    async def subscribe(self, subscriber: StreamingSubscriber, **kwargs) -> Awaitable[None]:
        with await self._subscribers_lock:
            if not self._subscribers:
                await self._before_first_subscriber()
            self._subscribers.append(subscriber)

    async def _before_first_subscriber(self) -> Awaitable[None]:
        pass

    async def unsubscribe(self, subscriber: StreamingSubscriber) -> Awaitable[None]:
        with await self._subscribers_lock:
            self._subscribers.remove(subscriber)
            if not self._subscribers:
                await self._after_last_subscriber()

    async def _after_last_subscriber(self) -> Awaitable[None]:
        pass

    async def _run(self) -> Awaitable[None]:
        while True:
            item = await self._queue.get()
            if item is None:
                break

            with await self._subscribers_lock:
                if not self._subscribers:
                    LOG.debug(
                        f"streaming facility '{self._name}': got item, but "
                        f"no subscribers were found, skip (item={repr(item)})"
                    )
                    continue

                try:
                    awaitables = [
                        subscriber.write(item)
                        for subscriber in self._subscribers
                    ]
                    await asyncio.gather(*awaitables, loop=self._loop)
                except:
                    LOG.exception(
                        f"streaming facility '{self._name}': failed to handle "
                        f"item (item={repr(item)})"
                    )

    def stop(self) -> None:
        LOG.debug(f"streaming facility '{self._name}': asked to stop")

        if self._main_task:
            self._queue.put_nowait(None)


class ChatStreamingFacility(QueueStreamingFacility):

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


class EventsStreamingFacility(QueueStreamingFacility):

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


class NotParsedStringsStreamingFacility(QueueStreamingFacility):

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

    def _consume(self, item: NotParsedGameLogString) -> None:
        item = TimestampedData(item)
        self._queue.put_nowait(item)


class _PeriodicSubscribers(list):

    def __init__(self, refresh_period: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refresh_period = refresh_period
        self._last_refresh_time = None

    def needs_refresh(self, when: float) -> bool:
        return (
            (self._last_refresh_time is None) or
            (when - self._last_refresh_time) >= self._refresh_period
        )

    def ack_refresh(self, when: float):
        if self._last_refresh_time is None:
            self._last_refresh_time = when
        else:
            elapsed_time = (when - self._last_refresh_time)
            _, buzz = divmod(elapsed_time, self._refresh_period)
            self._last_refresh_time = (when - buzz)


class RadarStreamingFacility(StreamingFacility):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        radar: Radar,
        request_timeout: Optional[float]=None,
        name: str="radar",
    ):
        super().__init__(loop=loop, name=name)

        self._radar = radar
        self._request_timeout = request_timeout

        self._do_stop = False

        self._resume_event = asyncio.Event(loop=loop)
        self._resume_event.clear()

        self._tick_task = None
        self._tick_period = None
        self._tick_period_lock = asyncio.Lock(loop=loop)

        self._refresh_task = None

        self._subscribers = dict()
        self._subscribers_lock = asyncio.Lock(loop=loop)

    async def subscribe(
        self,
        subscriber: StreamingSubscriber,
        refresh_period: float=5,
        **kwargs
    ) -> Awaitable[None]:
        with await self._subscribers_lock:
            group = self._subscribers.get(refresh_period)

            if group is None:
                group = _PeriodicSubscribers(refresh_period, [subscriber, ])
                self._subscribers[refresh_period] = group
                await self._maybe_set_new_tick_period()
            else:
                group.append(subscriber)

            if not self._resume_event.is_set():
                LOG.debug(f"streaming facility '{self._name}': resume")
                self._resume_event.set()

    async def unsubscribe(self, subscriber: StreamingSubscriber) -> Awaitable[None]:
        # TODO: refactor

        with await self._subscribers_lock:
            for refresh_period, group in self._subscribers.items():
                if subscriber in group:
                    group.remove(subscriber)

                    if not group:
                        del self._subscribers[refresh_period]

                    if self._subscribers:
                        await self._maybe_set_new_tick_period()
                    else:
                        if not self._do_stop:
                            LOG.debug(
                                f"streaming facility '{self._name}': pause"
                            )
                            self._resume_event.clear()

                        if self._tick_task:
                            self._tick_task.cancel()
                        elif self._refresh_task:
                            self._refresh_task.cancel()

                    break

    async def _maybe_set_new_tick_period(self) -> Awaitable[None]:
        refresh_periods = self._subscribers.keys()
        tick_period = functools.reduce(math.gcd, refresh_periods)

        with await self._tick_period_lock:
            if self._tick_period != tick_period:
                LOG.debug(
                    f"streaming facility '{self._name}': set new tick period "
                    f"(tick_period={tick_period})"
                )
                self._tick_period = tick_period

    async def _run(self) -> Awaitable[None]:
        # TODO: refactor

        while True:
            if self._do_stop:
                break
            elif not self._resume_event.is_set():
                await self._resume_event.wait()
                if self._do_stop:
                    break

            with await self._tick_period_lock:
                tick_period = self._tick_period

            try:
                coroutine = asyncio.sleep(tick_period, loop=self._loop)
                self._tick_task = asyncio.ensure_future(coroutine, loop=self._loop)
                await self._tick_task
            except CancelledError:
                LOG.debug(
                    f"streaming facility '{self._name}': tick task "
                    f"was cancelled"
                )
            finally:
                self._tick_task = None

            if self._do_stop:
                break
            elif not self._resume_event.is_set():
                await self._resume_event.wait()
                if self._do_stop:
                    break

            now = time.monotonic()
            do_refresh = any(
                group.needs_refresh(now)
                for group in self._subscribers.values()
            )
            if not do_refresh:
                continue

            try:
                coroutine = self._radar.get_all_moving_actors_positions(
                    timeout=self._request_timeout,
                )
                self._refresh_task = asyncio.ensure_future(
                    coroutine,
                    loop=self._loop,
                )
                data = await self._refresh_task
            except CancelledError:
                LOG.debug(
                    f"streaming facility '{self._name}': refresh task "
                    f"was cancelled"
                )
            except ConnectionAbortedError:
                LOG.debug(
                    f"streaming facility '{self._name}': connection with radar"
                    f"was lost"
                )
                break
            finally:
                self._refresh_task = None

            if self._do_stop:
                break
            elif not self._resume_event.is_set():
                await self._resume_event.wait()
                if self._do_stop:
                    break
                else:
                    continue

            if data.is_empty:
                LOG.debug(
                    f"streaming facility '{self._name}': empty data, skip"
                )
                continue

            item = TimestampedData(data)
            now = time.monotonic()

            for group in self._subscribers.values():
                if group.needs_refresh(now):
                    try:
                        awaitables = [
                            subscriber.write(item)
                            for subscriber in group
                        ]
                        await asyncio.gather(*awaitables, loop=self._loop)
                    except:
                        LOG.exception(
                            f"streaming facility '{self._name}': failed to "
                            f"handle item (item={repr(item)})"
                        )
                    else:
                        group.ack_refresh(now)

    def stop(self) -> None:
        LOG.debug(f"streaming facility '{self._name}': asked to stop")

        self._do_stop = True
        self._resume_event.set()

        if self._tick_task:
            self._tick_task.cancel()

        if self._refresh_task:
            self._refresh_task.cancel()
