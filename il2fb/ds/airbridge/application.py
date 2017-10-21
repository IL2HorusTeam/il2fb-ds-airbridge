# coding: utf-8

import asyncio
import logging
import threading

from pathlib import Path
from typing import Awaitable, Callable

from ddict import DotAccessDict

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from il2fb.ds.airbridge.dedicated_server.console import ConsoleProxy
from il2fb.ds.airbridge.dedicated_server.device_link import DeviceLinkProxy
from il2fb.ds.airbridge.dedicated_server.process import DedicatedServer
from il2fb.ds.airbridge.typing import IntOrNone, StringHandler
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

        self._game_log_watch_dog = None
        self._game_log_watch_dog_thread = None

    async def start(self) -> Awaitable[None]:
        await self._maybe_start_console_client_proxy()
        await self._maybe_start_device_link_client_proxy()
        self._start_game_log_processing()

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

    def _start_game_log_processing(self):
        file_path = Path(self._dedicated_server.config.events.logging.file_name)

        if not file_path.is_absolute():
            file_path = self._dedicated_server.root_dir / file_path

        file_path = file_path.absolute()

        self._game_log_watch_dog = TextFileWatchDog(
            path=file_path,
            state=self._state.game_log_watch_dog,
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

    async def wait_stopped(self) -> Awaitable[IntOrNone]:
        awaitables = []

        if self._console_client_proxy:
            awaitables.append(self._console_client_proxy.wait_stopped())

        if self._device_link_client_proxy:
            awaitables.append(self._device_link_client_proxy.wait_stopped())

        if awaitables:
            await asyncio.gather(*awaitables, loop=self._loop)

        if self._game_log_watch_dog_thread:
            self._game_log_watch_dog_thread.join()
