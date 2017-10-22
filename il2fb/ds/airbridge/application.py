# coding: utf-8

import asyncio
import logging
import threading
import queue

from pathlib import Path
from typing import Awaitable, Callable

import janus

from ddict import DotAccessDict
from il2fb.commons.events import Event
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient
from il2fb.parsers.game_log.parsers import GameLogEventParser

from il2fb.ds.airbridge.dedicated_server.console import ConsoleProxy
from il2fb.ds.airbridge.dedicated_server.device_link import DeviceLinkProxy
from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker
from il2fb.ds.airbridge.dedicated_server.process import DedicatedServer
from il2fb.ds.airbridge.streaming.facilities import (
    ChatStreamingFacility, EventsStreamingFacility,
)
from il2fb.ds.airbridge.structures import TimestampedItem
from il2fb.ds.airbridge.typing import (
    StringHandler, AsyncTimestampedItemHandler,
)
from il2fb.ds.airbridge.watch_dog import TextFileWatchDog


LOG = logging.getLogger(__name__)


class Airbridge:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        config: DotAccessDict,
        state: DotAccessDict,
        dedicated_server: DedicatedServer,
        console_client: ConsoleClient,
        device_link_client: DeviceLinkClient,
    ):
        self._loop = loop
        self._config = config
        self._state = state

        self._dedicated_server = dedicated_server

        self._console_client = console_client
        self._console_client_proxy = None

        self._device_link_client = device_link_client
        self._device_link_client_proxy = None

        self._game_log_string_queue = queue.Queue()
        self._game_log_event_parser = GameLogEventParser()

        self._game_log_worker = GameLogWorker(
            string_producer=self._game_log_string_queue.get,
            string_parser=self._game_log_event_parser.parse,
        )
        self._game_log_worker_thread = None

        self._game_log_watch_dog = None
        self._game_log_watch_dog_thread = None

        self.chat = ChatStreamingFacility(
            loop=loop,
            console_client=console_client,
        )
        self.events = EventsStreamingFacility(
            loop=loop,
            console_client=console_client,
            game_log_worker=self._game_log_worker,
        )

        self._not_parsed_strings_queue = janus.Queue(loop=loop)
        self._not_parsed_strings_subscribers_lock = asyncio.Lock(loop=loop)
        self._not_parsed_strings_subscribers = []
        self._not_parsed_strings_processing_task = None

    async def subscribe_to_not_parsed_strings(
        self,
        subscriber: AsyncTimestampedItemHandler,
    ) -> Awaitable[None]:
        with await self._not_parsed_strings_subscribers_lock:
            if not self._not_parsed_strings_subscribers:
                self._game_log_worker.subscribe_to_not_parsed_strings(
                    subscriber=self._handle_not_parsed_string,
                )
            self._not_parsed_strings_subscribers.append(subscriber)

    async def unsubscribe_from_not_parsed_strings(
        self,
        subscriber: AsyncTimestampedItemHandler,
    ) -> Awaitable[None]:
        with await self._not_parsed_strings_subscribers_lock:
            self._not_parsed_strings_subscribers.remove(subscriber)
            if not self._not_parsed_strings_subscribers:
                self._game_log_worker.unsubscribe_from_not_parsed_strings(
                    subscriber=self._handle_not_parsed_string,
                )

    def _handle_not_parsed_string(self, s: str) -> None:
        item = TimestampedItem(s)
        self._not_parsed_strings_queue.sync_q.put_nowait(item)

    async def start(self) -> Awaitable[None]:
        await self._maybe_start_console_client_proxy()
        await self._maybe_start_device_link_client_proxy()

        self._start_subscribers_serving()
        self._start_game_log_worker()
        self._start_game_log_watch_dog()

    async def _maybe_start_console_client_proxy(self) -> None:
        console_proxy_config = self._config.ds.console_proxy
        if console_proxy_config:
            self._console_client_proxy = ConsoleProxy(
                loop=self._loop,
                config=console_proxy_config,
                console_client=self._console_client,
            )
            await self._console_client_proxy.start()

    async def _maybe_start_device_link_client_proxy(self) -> None:
        device_link_proxy_config = self._config.ds.device_link_proxy
        if device_link_proxy_config:
            self._device_link_client_proxy = DeviceLinkProxy(
                loop=self._loop,
                config=device_link_proxy_config,
                device_link_client=self._device_link_client,
            )
            await self._device_link_client_proxy.start()

    def _start_subscribers_serving(self):
        self.chat.start()
        self.events.start()

        self._not_parsed_strings_processing_task = self._loop.create_task(
            self._process_not_parsed_strings(),
        )

    async def _process_not_parsed_strings(self):
        while True:
            item = await self._not_parsed_strings_queue.async_q.get()
            if item is None:
                break

            with await self._not_parsed_strings_subscribers_lock:
                for subscriber in self._not_parsed_strings_subscribers:
                    try:
                        result = subscriber(item)
                        if asyncio.iscoroutine(result):
                            await result
                    except:
                        LOG.exception(
                            f"subscriber failed to handle not parsered string "
                            f"(item={repr(item)})"
                        )

    def _start_game_log_worker(self):
        self._game_log_worker_thread = threading.Thread(
            target=self._game_log_worker.run,
            daemon=True,
        )
        self._game_log_worker_thread.start()

    def _start_game_log_watch_dog(self):
        file_path = Path(self._dedicated_server.config.events.logging.file_name)

        if not file_path.is_absolute():
            file_path = self._dedicated_server.root_dir / file_path

        file_path = file_path.absolute()

        self._game_log_watch_dog = TextFileWatchDog(
            path=file_path,
            state=self._state.game_log_watch_dog,
        )
        self._game_log_watch_dog.subscribe(
            subscriber=self._game_log_string_queue.put_nowait,
        )
        self._game_log_watch_dog_thread = threading.Thread(
            target=self._game_log_watch_dog.run,
            daemon=True,
        )
        self._game_log_watch_dog_thread.start()

    def stop(self) -> None:
        if self._console_client_proxy:
            self._console_client_proxy.stop()

        if self._device_link_client_proxy:
            self._device_link_client_proxy.stop()

        if self._game_log_watch_dog:
            self._game_log_watch_dog.stop()

    async def wait_stopped(self) -> Awaitable[None]:
        awaitables = []

        if self._console_client_proxy:
            awaitables.append(self._console_client_proxy.wait_stopped())

        if self._device_link_client_proxy:
            awaitables.append(self._device_link_client_proxy.wait_stopped())

        if awaitables:
            await asyncio.gather(*awaitables, loop=self._loop)

        if self._game_log_watch_dog_thread:
            self._game_log_watch_dog_thread.join()

        if self._game_log_worker_thread:
            self._game_log_string_queue.put_nowait(None)
            self._game_log_worker_thread.join()

        self.chat.stop()
        self.events.stop()

        await self.chat.wait_stopped()
        await self.events.wait_stopped()

        awaitables = []

        if self._not_parsed_strings_processing_task:
            self._not_parsed_strings_queue.async_q.put_nowait(None)
            awaitables.append(self._not_parsed_strings_processing_task)

        if awaitables:
            await asyncio.gather(*awaitables, loop=self._loop)
