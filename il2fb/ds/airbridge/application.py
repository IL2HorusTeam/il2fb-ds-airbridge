# coding: utf-8

import asyncio
import logging

from typing import Awaitable, Callable

from ddict import DotAccessDict

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from il2fb.ds.airbridge.dedicated_server.console import ConsoleProxy
from il2fb.ds.airbridge.dedicated_server.device_link import DeviceLinkProxy
from il2fb.ds.airbridge.dedicated_server.process import DedicatedServer
from il2fb.ds.airbridge.typing import IntOrNone


LOG = logging.getLogger(__name__)


StringHandler = Callable[[str], None]


class Airbridge:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        config: DotAccessDict,
        dedicated_server: DedicatedServer,
        console_client: ConsoleClient,
        device_link_client: DeviceLinkClient,
    ):
        self._loop = loop
        self._config = config
        self._dedicated_server = dedicated_server

        self._console_client = console_client
        self._console_client_proxy = None

        self._device_link_client = device_link_client
        self._device_link_client_proxy = None

    async def run(self) -> Awaitable[None]:
        self._maybe_create_console_client_proxy()
        self._maybe_create_device_link_client_proxy()

    def _maybe_create_console_client_proxy(self) -> None:
        console_proxy_config = self._config.ds.console
        if console_proxy_config:
            self._console_proxy = ConsoleProxy(
                loop=self._loop,
                config=console_proxy_config,
                console_client=self._console_client,
            )
            future = self._console_proxy.run()
            self._loop.create_task(future)

    def _maybe_create_device_link_client_proxy(self) -> None:
        device_link_proxy_config = self._config.ds.device_link
        if device_link_proxy_config:
            self._device_link_proxy = DeviceLinkProxy(
                loop=self._loop,
                config=device_link_proxy_config,
                device_link_client=self._device_link_client,
            )
            future = self._device_link_proxy.run()
            self._device_link_proxy_task = self._loop.create_task(future)

    def exit(self) -> None:
        if self._console_client_proxy:
            self._console_client_proxy.exit()

        if self._device_link_client_proxy:
            self._device_link_client_proxy.exit()

    async def wait_exit(self) -> Awaitable[IntOrNone]:
        awaitables = []

        if self._console_client_proxy:
            awaitables.append(self._console_client_proxy.wait_exit())

        if self._device_link_client_proxy:
            awaitables.append(self._device_link_client_proxy.wait_exit())

        if awaitables:
            await asyncio.gather(*awaitables, loop=self._loop)
