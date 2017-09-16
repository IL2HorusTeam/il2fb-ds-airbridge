# coding: utf-8

import asyncio
import logging

from typing import Awaitable, Callable, Optional

import psutil

from ddict import DotAccessDict
from funcy import log_calls

from il2fb.config.ds import ServerConfig
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from .dedicated_server import DedicatedServer
from .exceptions import AirbridgeException


LOG = logging.getLogger(__name__)


StringHandler = Callable[[str], None]


def validate_dedicated_server_config(config: ServerConfig) -> None:
    if not config.console.connection.port:
        raise ValueError(
            "server's console is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#console-section)"
        )

    if not config.device_link.connection.port:
        raise ValueError(
            "server's device link is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#devicelink-section)"
        )


@log_calls(LOG.debug, errors=False)
async def wait_for_dedicated_server_ports(
    loop: asyncio.AbstractEventLoop,
    pid: int,
    config: ServerConfig,
    timeout: float=3,
) -> Awaitable[None]:

    process = psutil.Process(pid)
    expected_ports = {
        config.connection.port,
        config.console.connection.port,
        config.device_link.connection.port,
    }

    while timeout > 0:
        start_time = loop.time()

        actual_ports = {c.laddr.port for c in process.connections('inet')}
        if actual_ports == expected_ports:
            return

        delay = min(timeout, 0.1)
        await asyncio.sleep(delay, loop=loop)

        time_delta = loop.time() - start_time
        timeout = max(0, timeout - time_delta)

    raise RuntimeError("expected ports of dedicated server are closed")


class Airbridge:

    def __init__(
        self,

        loop: asyncio.AbstractEventLoop,
        config: DotAccessDict,

        stdout_handler: StringHandler=None,
        stderr_handler: StringHandler=None,
        passive_prompt_handler: StringHandler=None,
        active_prompt_handler: StringHandler=None,
    ):
        self._loop = loop
        self._config = config

        self._stdout_handler = stdout_handler
        self._stderr_handler = stderr_handler
        self._passive_prompt_handler = passive_prompt_handler
        self._active_prompt_handler = active_prompt_handler

        self._dedicated_server = None
        self._dedicated_server_task = None

        self._console_client = None
        self._console_task = None

        self._device_link_client = None
        self._device_link_task = None

        self._boot_future = asyncio.Future()

    async def run(self) -> Awaitable[None]:
        try:
            await self._boot()
        except Exception as e:
            self._boot_future.set_exception(e)
            return
        else:
            self._boot_future.set_result(None)

        return_code = await self._dedicated_server_task

        self._console_client.close()
        self._device_link_client.close()

        await asyncio.gather(
            self._console_client.wait_closed(),
            self._device_link_client.wait_closed(),
            loop=self._loop,
        )

        if return_code != 0:
            LOG.fatal(f"dedicated server has exited with code {return_code}")
            raise AirbridgeException

    async def _boot(self) -> Awaitable[None]:
        await self._boot_dedicated_server()
        await self._connect_to_server()

    async def _boot_dedicated_server(self) -> Awaitable[None]:
        try:
            self._dedicated_server = DedicatedServer(
                loop=self._loop,

                exe_path=self._config.ds.exe_path,
                config_path=self._config.ds.get('config_path'),
                start_script_path=self._config.ds.get('start_script_path'),
                wine_bin_path=self._config.wine_bin_path,

                stdout_handler=self._stdout_handler,
                stderr_handler=self._stderr_handler,
                passive_prompt_handler=self._passive_prompt_handler,
                active_prompt_handler=self._active_prompt_handler,
            )
        except Exception:
            LOG.fatal("failed to init dedicated server", exc_info=True)
            raise AirbridgeException

        try:
            validate_dedicated_server_config(self._dedicated_server.config)
        except ValueError as e:
            LOG.fatal(e)
            raise AirbridgeException

        future = self._dedicated_server.run()
        self._dedicated_server_task = self._loop.create_task(future)

        try:
            await self._dedicated_server.wait_for_start()
        except Exception:
            self._dedicated_server_task.cancel()
            LOG.fatal("failed to start dedicated server", exc_info=True)
            raise AirbridgeException

        try:
            await wait_for_dedicated_server_ports(
                self._loop,
                self._dedicated_server.pid,
                self._dedicated_server.config,
            )
        except Exception as e:
            LOG.fatal(e)
            self._dedicated_server.terminate()
            await self._dedicated_server_task
            raise AirbridgeException

    async def _connect_to_server(self) -> Awaitable[None]:
        config = self._dedicated_server.config

        self._console_client = ConsoleClient()
        future = self._loop.create_connection(
            protocol_factory=lambda: self._console_client,
            host=(config.connection.host or "localhost"),
            port=config.console.connection.port,
        )
        self._console_task = self._loop.create_task(future)

        remote_address = (
            (config.device_link.connection.host or "localhost"),
            config.device_link.connection.port,
        )
        self._device_link_client = DeviceLinkClient(remote_address)
        future = self._loop.create_datagram_endpoint(
            protocol_factory=lambda: self._device_link_client,
            remote_addr=remote_address,
        )
        self._device_link_task = self._loop.create_task(future)

        await asyncio.gather(
            self._console_client.wait_connected(),
            self._device_link_client.wait_connected(),
            loop=self._loop,
        )

    def ask_exit(self) -> None:
        if self._dedicated_server_task:
            self._dedicated_server.terminate()

        if self._console_task:
            self._console_client.close()

        if self._device_link_task:
            self._device_link_client.close()

    async def wait_exit(self) -> Awaitable[Optional[int]]:
        if not self._dedicated_server_task:
            return

        dedicated_server_future = self._dedicated_server.wait_for_exit()
        awaitables = [dedicated_server_future, ]

        if self._console_task:
            awaitables.append(self._console_client.wait_closed())

        if self._device_link_task:
            awaitables.append(self._device_link_client.wait_closed())

        results = await asyncio.gather(*awaitables)
        return_code = results[0]

        return return_code

    def wait_boot(self) -> Awaitable[None]:
        return self._boot_future

    def user_input(self, s: str) -> Awaitable[None]:
        return self._dedicated_server.input(s)
