# coding: utf-8

import asyncio
import itertools
import logging
import threading
import queue

from typing import Awaitable

from ddict import DotAccessDict
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient
from il2fb.parsers.game_log.parsers import GameLogEventParser

from il2fb.ds.airbridge.dedicated_server.console import ConsoleProxy
from il2fb.ds.airbridge.dedicated_server.device_link import DeviceLinkProxy
from il2fb.ds.airbridge.dedicated_server.instance import DedicatedServer
from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker

from il2fb.ds.airbridge.api.nats import NATSSubscriber

from il2fb.ds.airbridge.nats import NATSClient
from il2fb.ds.airbridge.nats import NATSStreamingClient

from il2fb.ds.airbridge.radar import Radar

from il2fb.ds.airbridge.streaming.facilities import ChatStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import EventsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import NotParsedStringsStreamingFacility

from il2fb.ds.airbridge.streaming.subscribers.loaders import load_subscribers_from_config
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
        trace: bool=False,
    ):
        self.loop = loop

        self._config = config
        self._state = state
        self._trace = trace

        self.dedicated_server = dedicated_server

        self.console_client = console_client
        self._console_client_proxy = None

        self.device_link_client = device_link_client
        self._device_link_client_proxy = None

        self.radar = Radar(
            device_link_client=self.device_link_client,
        )

        self._game_log_string_queue = queue.Queue()
        self._game_log_event_parser = GameLogEventParser()

        self._game_log_worker = GameLogWorker(
            string_producer=self._game_log_string_queue.get,
            string_parser=self._game_log_event_parser.parse,
        )
        self._game_log_worker_thread = None

        self._game_log_watch_dog = TextFileWatchDog(
            path=self.dedicated_server.game_log_path,
            state=self._state.game_log_watch_dog,
        )
        self._game_log_watch_dog.subscribe(
            subscriber=self._game_log_string_queue.put_nowait,
        )
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
        self.not_parsed_strings = NotParsedStringsStreamingFacility(
            loop=loop,
            game_log_worker=self._game_log_worker,
        )

        self._streaming_subscribers = {
            self.chat: load_subscribers_from_config(
                app=self,
                config=config.streaming.chat,
            ),
            self.events: load_subscribers_from_config(
                app=self,
                config=config.streaming.events,
            ),
            self.not_parsed_strings: load_subscribers_from_config(
                app=self,
                config=config.streaming.not_parsed_strings,
            ),
        }

        self.nats_client = None
        self.nats_streaming_client = None
        self._nats_subscriber = None

    async def start(self) -> Awaitable[None]:
        await self._maybe_start_nats_clients()
        await self._maybe_start_streaming_subscribers()
        self._start_streaming_facilities()
        self._start_game_log_processing()
        await self._maybe_start_proxies()

    async def _maybe_start_nats_clients(self) -> Awaitable[None]:
        config = self._config.nats
        if not config:
            return

        self.nats_client = NATSClient(loop=self.loop)
        await self.nats_client.connect(servers=config.servers)

        subscription_config = config.subscription
        if subscription_config:
            self._nats_subscriber = NATSSubscriber(
                nats_client=self.nats_client,
                subject=subscription_config.subject,
                console_client=self.console_client,
                radar=self.radar,
                trace=self._trace,
            )
            await self._nats_subscriber.start()

        streaming_config = config.streaming
        if not streaming_config:
            return

        self.nats_streaming_client = NATSStreamingClient(
            loop=self.loop,
            nats_client=self.nats_client,
        )
        await self.nats_streaming_client.connect(
            cluster_id=streaming_config.cluster_id,
            client_id=streaming_config.client_id,
        )

    async def _maybe_start_streaming_subscribers(self) -> Awaitable[None]:
        subscriber_groups = self._streaming_subscribers.values()
        subscribers = list(itertools.chain(*subscriber_groups))

        if not subscribers:
            return

        for subscriber in subscribers:
            subscriber.open()

        awaitables = [
            subscriber.wait_opened()
            for subscriber in subscribers
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

        awaitables = [
            facility.subscribe(subscriber.write)
            for facility, subscriber_group in self._streaming_subscribers.items()
            for subscriber in subscriber_group
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

    def _start_streaming_facilities(self) -> None:
        self.chat.start()
        self.events.start()
        self.not_parsed_strings.start()

    def _start_game_log_processing(self) -> None:
        self._start_game_log_worker()
        self._start_game_log_watch_dog()

    def _start_game_log_worker(self) -> None:
        self._game_log_worker_thread = threading.Thread(
            target=self._game_log_worker.run,
            name="log worker",
            daemon=True,
        )
        self._game_log_worker_thread.start()

    def _start_game_log_watch_dog(self) -> None:
        self._game_log_watch_dog_thread = threading.Thread(
            target=self._game_log_watch_dog.run,
            name="log watcher",
            daemon=True,
        )
        self._game_log_watch_dog_thread.start()

    async def _maybe_start_proxies(self) -> Awaitable[None]:
        await asyncio.gather(
            self._maybe_start_console_client_proxy(),
            self._maybe_start_device_link_client_proxy(),
            loop=self.loop,
        )

    async def _maybe_start_console_client_proxy(self) -> Awaitable[None]:
        console_proxy_config = self._config.ds.console_proxy
        if console_proxy_config:
            self._console_client_proxy = ConsoleProxy(
                loop=self.loop,
                config=console_proxy_config,
                console_client=self.console_client,
            )
            await self._console_client_proxy.start()

    async def _maybe_start_device_link_client_proxy(self) -> None:
        device_link_proxy_config = self._config.ds.device_link_proxy
        if device_link_proxy_config:
            self._device_link_client_proxy = DeviceLinkProxy(
                loop=self.loop,
                config=device_link_proxy_config,
                device_link_client=self.device_link_client,
            )
            await self._device_link_client_proxy.start()

    def stop(self) -> None:
        self._maybe_stop_proxies()
        self._game_log_watch_dog.stop()

    def _maybe_stop_proxies(self) -> None:
        if self._console_client_proxy:
            self._console_client_proxy.stop()

        if self._device_link_client_proxy:
            self._device_link_client_proxy.stop()

    async def wait_stopped(self) -> Awaitable[None]:
        await self._maybe_wait_proxies()
        self._maybe_stop_game_log_processing()
        await self._stop_streaming_facilities()
        await self._maybe_stop_streaming_subscribers()
        await self._maybe_stop_nats_clients()

    async def _maybe_wait_proxies(self) -> Awaitable[None]:
        awaitables = []

        if self._console_client_proxy:
            awaitables.append(self._console_client_proxy.wait_stopped())

        if self._device_link_client_proxy:
            awaitables.append(self._device_link_client_proxy.wait_stopped())

        if awaitables:
            await asyncio.gather(*awaitables, loop=self.loop)

    def _maybe_stop_game_log_processing(self) -> None:
        if self._game_log_watch_dog_thread:
            self._game_log_watch_dog_thread.join()

        if self._game_log_worker_thread:
            self._game_log_string_queue.put_nowait(None)
            self._game_log_worker_thread.join()

    async def _stop_streaming_facilities(self) -> Awaitable[None]:
        self.chat.stop()
        self.events.stop()
        self.not_parsed_strings.stop()

        await self._wait_streaming_facilities()

    async def _wait_streaming_facilities(self) -> Awaitable[None]:
        await asyncio.gather(
            self.chat.wait_stopped(),
            self.events.wait_stopped(),
            self.not_parsed_strings.wait_stopped(),
            loop=self.loop,
        )

    async def _maybe_stop_streaming_subscribers(self) -> Awaitable[None]:
        subscriber_groups = self._streaming_subscribers.values()
        subscribers = list(itertools.chain(*subscriber_groups))

        if not subscribers:
            return

        awaitables = [
            facility.unsubscribe(subscriber.write)
            for facility, subscriber_group in self._streaming_subscribers.items()
            for subscriber in subscriber_group
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

        for subscriber in subscribers:
            subscriber.close()

        awaitables = [
            subscriber.wait_closed()
            for subscriber in subscribers
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

    async def _maybe_stop_nats_clients(self) -> Awaitable[None]:
        if not self.nats_client or self.nats_client.is_closed:
            return

        if self.nats_streaming_client:
            await self.nats_streaming_client.close()

        if self._nats_subscriber:
            await self._nats_subscriber.stop()

        await self.nats_client.flush()
        await self.nats_client.close()
