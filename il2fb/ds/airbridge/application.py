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
from il2fb.parsers.mission import MissionParser

from il2fb.ds.airbridge.dedicated_server.console import ConsoleProxy
from il2fb.ds.airbridge.dedicated_server.device_link import DeviceLinkProxy
from il2fb.ds.airbridge.dedicated_server.instance import DedicatedServer
from il2fb.ds.airbridge.dedicated_server.game_log import GameLogWorker

from il2fb.ds.airbridge.api.http import build_http_api
from il2fb.ds.airbridge.api.http.security import AuthorizationBackend
from il2fb.ds.airbridge.api.nats import NATSSubscriber

from il2fb.ds.airbridge.nats import NATSClient
from il2fb.ds.airbridge.nats import NATSStreamingClient

from il2fb.ds.airbridge.radar import Radar

from il2fb.ds.airbridge.streaming.facilities import ChatStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import EventsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import NotParsedStringsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import RadarStreamingFacility

from il2fb.ds.airbridge.streaming.subscribers.loaders import load_subscribers_with_subscription_options
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

        self._mission_parser = MissionParser()

        self._game_log_event_parser = GameLogEventParser()
        self._game_log_string_queue = queue.Queue()

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

        self.chat_stream = ChatStreamingFacility(
            loop=loop,
            console_client=console_client,
        )
        self.events_stream = EventsStreamingFacility(
            loop=loop,
            console_client=console_client,
            game_log_worker=self._game_log_worker,
        )
        self.not_parsed_strings_stream = NotParsedStringsStreamingFacility(
            loop=loop,
            game_log_worker=self._game_log_worker,
        )
        self.radar_stream = RadarStreamingFacility(
            loop=loop,
            radar=self.radar,
            request_timeout=config.streaming.radar.get('request_timeout'),
        )

        self.nats_client = None
        self.nats_streaming_client = None

        self._nats_api = None

        self._http_api = None
        self._http_api_handler = None
        self._http_api_server = None

        self._streaming_facility_to_static_subscribers_config_map = {
            self.chat_stream: config.streaming.chat.subscribers,
            self.events_stream: config.streaming.events.subscribers,
            self.not_parsed_strings_stream: config.streaming.not_parsed_strings.subscribers,
            self.radar_stream: config.streaming.radar.subscribers,
        }
        self._static_streaming_subscribers = {}

    async def start(self) -> Awaitable[None]:
        await self._maybe_start_nats_clients()
        await self._maybe_start_static_streaming_subscribers()
        self._start_streaming_facilities()
        self._start_game_log_processing()
        await self._maybe_start_proxies()
        await self._maybe_start_api()

    async def _maybe_start_nats_clients(self) -> Awaitable[None]:
        config = self._config.nats
        if not config:
            return

        self.nats_client = NATSClient(loop=self.loop)
        await self.nats_client.connect(servers=config.servers)

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

    async def _maybe_start_static_streaming_subscribers(self) -> Awaitable[None]:
        for facility, config in self._streaming_facility_to_static_subscribers_config_map.items():
            subscribers_with_subscription_options = load_subscribers_with_subscription_options(
                app=self,
                config=config,
            )

            if not subscribers_with_subscription_options:
                continue

            subscribers = list(zip(*subscribers_with_subscription_options))[0]
            self._static_streaming_subscribers[facility] = subscribers

            for subscriber in subscribers:
                subscriber.plug_in()

            awaitables = [
                subscriber.wait_plugged()
                for subscriber in subscribers
            ]
            await asyncio.gather(*awaitables, loop=self.loop)

            awaitables = [
                facility.subscribe(subscriber, **options)
                for subscriber, options in subscribers_with_subscription_options
            ]
            await asyncio.gather(*awaitables, loop=self.loop)

    def _start_streaming_facilities(self) -> None:
        self.chat_stream.start()
        self.events_stream.start()
        self.not_parsed_strings_stream.start()
        self.radar_stream.start()

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

    async def _maybe_start_device_link_client_proxy(self) -> Awaitable[None]:
        device_link_proxy_config = self._config.ds.device_link_proxy
        if device_link_proxy_config:
            self._device_link_client_proxy = DeviceLinkProxy(
                loop=self.loop,
                config=device_link_proxy_config,
                device_link_client=self.device_link_client,
            )
            await self._device_link_client_proxy.start()

    async def _maybe_start_api(self) -> Awaitable[None]:
        await self._maybe_start_nats_api()
        await self._maybe_start_http_api()

    async def _maybe_start_nats_api(self) -> Awaitable[None]:
        if not self.nats_client:
            return

        config = self._config.api.nats
        if config:
            self._nats_api = NATSSubscriber(
                nats_client=self.nats_client,
                subject=config.subject,
                console_client=self.console_client,
                radar=self.radar,
                trace=self._trace,
            )
            await self._nats_api.start()

    async def _maybe_start_http_api(self) -> Awaitable[None]:
        config = self._config.api.http

        if not config:
            return

        api_options = dict(
            loop=self.loop,
            dedicated_server=self.dedicated_server,
            console_client=self.console_client,
            radar=self.radar,
            chat_stream=self.chat_stream,
            events_stream=self.events_stream,
            not_parsed_strings_stream=self.not_parsed_strings_stream,
            radar_stream=self.radar_stream,
            mission_parser=self._mission_parser,
            cors_options=config.cors,
            debug=self._trace,
        )

        auth_options = config.auth
        if auth_options:
            backend = AuthorizationBackend(
                token_storage_path=auth_options.token_storage_path,
                token_header_name=auth_options.get('token_header_name')
            )
            api_options['authorization_backend'] = backend

        self._http_api = build_http_api(**api_options)
        self._http_api_handler = self._http_api.make_handler(
            loop=self.loop,
        )
        self._http_api_server = await self.loop.create_server(
            self._http_api_handler,
            config.bind.address or "localhost",
            config.bind.port,
        )

    async def stop(self) -> Awaitable[None]:
        await self._maybe_stop_proxies()
        self._game_log_watch_dog.stop()
        await self._maybe_stop_api()
        self._maybe_stop_game_log_processing()
        await self._stop_streaming_facilities()
        await self._maybe_stop_static_streaming_subscribers()
        await self._maybe_stop_nats_clients()

    async def _maybe_stop_proxies(self) -> None:
        awaitables = []

        if self._console_client_proxy:
            self._console_client_proxy.stop()
            awaitables.append(self._console_client_proxy.wait_stopped())

        if self._device_link_client_proxy:
            self._device_link_client_proxy.stop()
            awaitables.append(self._device_link_client_proxy.wait_stopped())

        if awaitables:
            await asyncio.gather(*awaitables, loop=self.loop)

    async def _maybe_stop_api(self) -> Awaitable[None]:
        await self._maybe_stop_nats_api()
        await self._maybe_stop_http_api()

    async def _maybe_stop_nats_api(self) -> Awaitable[None]:
        if self._nats_api:
            await self._nats_api.stop()

    async def _maybe_stop_http_api(self) -> Awaitable[None]:
        if self._http_api_server:
            self._http_api_server.close()
            await self._http_api_server.wait_closed()
            await self._http_api.shutdown()
            await self._http_api_handler.shutdown(60.0)
            await self._http_api.cleanup()

    def _maybe_stop_game_log_processing(self) -> None:
        if self._game_log_watch_dog_thread:
            self._game_log_watch_dog_thread.join()

        if self._game_log_worker_thread:
            self._game_log_string_queue.put_nowait(None)
            self._game_log_worker_thread.join()

    async def _stop_streaming_facilities(self) -> Awaitable[None]:
        self.chat_stream.stop()
        self.events_stream.stop()
        self.not_parsed_strings_stream.stop()
        self.radar_stream.stop()

        await self._wait_streaming_facilities()

    async def _wait_streaming_facilities(self) -> Awaitable[None]:
        await asyncio.gather(
            self.chat_stream.wait_stopped(),
            self.events_stream.wait_stopped(),
            self.not_parsed_strings_stream.wait_stopped(),
            self.radar_stream.wait_stopped(),
            loop=self.loop,
        )

    async def _maybe_stop_static_streaming_subscribers(self) -> Awaitable[None]:
        subscriber_groups = self._static_streaming_subscribers.values()
        subscribers = list(itertools.chain(*subscriber_groups))

        if not subscribers:
            return

        awaitables = [
            facility.unsubscribe(subscriber)
            for facility, subscriber_group in self._static_streaming_subscribers.items()
            for subscriber in subscriber_group
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

        for subscriber in subscribers:
            subscriber.unplug()

        awaitables = [
            subscriber.wait_unplugged()
            for subscriber in subscribers
        ]
        await asyncio.gather(*awaitables, loop=self.loop)

    async def _maybe_stop_nats_clients(self) -> Awaitable[None]:
        if not self.nats_client:
            return

        if self.nats_streaming_client:
            await self.nats_streaming_client.close()

        if self.nats_client.is_connected:
            await self.nats_client.flush()

        await self.nats_client.close()
