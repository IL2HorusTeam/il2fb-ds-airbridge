# coding: utf-8

import asyncio
import logging

from typing import Awaitable, Callable

from ddict import DotAccessDict

from il2fb.ds.middleware.console.client import ConsoleClient


LOG = logging.getLogger(__name__)


class ConsoleConnection(asyncio.Protocol):

    def __init__(self, loop: asyncio.AbstractEventLoop, registry):
        self._loop = loop
        self._registry = registry

        self._data_buffer = bytes()
        self._transport = None
        self._peer = None
        self._closed_ack = asyncio.Future(loop=self._loop)

        self._servers = []

    @property
    def peer(self):
        return self._peer

    def register_listener(self, listener: Callable[[bytes], None]) -> None:
        self._servers.append(listener)

    def unregister_listener(self, listener: Callable[[bytes], None]) -> None:
        self._servers.remove(listener)

    def connection_made(self, transport) -> None:
        self._transport = transport
        self._peer = transport.get_extra_info('peername')

        LOG.debug(f"con <-- {repr(self._peer)}")

        self._registry.register_connection(self)

    def connection_lost(self, exc: Exception) -> None:
        LOG.debug(f"con X-- {repr(self._peer)}")

        try:
            self._registry.unregister_connection(self)
        finally:
            self._closed_ack.set_result(None)

    def close(self) -> None:
        self._transport.close()

    def wait_closed(self) -> Awaitable[None]:
        return self._closed_ack

    def data_received(self, data: bytes) -> None:
        LOG.debug(f"dat <-- {repr(data)} from {self.peer}")

        buffer = self._data_buffer + data

        last_eol = buffer.rfind(b'\n')
        if last_eol < 0:
            return

        last_eol += 1
        data, self._data_buffer = buffer[:last_eol], buffer[last_eol:]

        if not data:
            return

        for listener in self._servers:
            try:
                listener(data)
            except Exception:
                LOG.exception(f"failed to feed data to listener {listener}")

    def write_bytes(self, data: bytes) -> None:
        self._transport.write(data)
        LOG.debug(f"dat --> {repr(data)} to {self.peer}")


class ConsoleProxy:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        config: DotAccessDict,
        console_client: ConsoleClient,
    ):
        self._loop = loop
        self._config = config
        self._console_client = console_client

        self._server = None
        self._connections = []

    async def run(self):
        self._server = await self._loop.create_server(
            lambda: ConsoleConnection(loop=self._loop, registry=self),
            (self._config.bind.address or "localhost"),
            self._config.bind.port,
        )
        await self._server.wait_closed()

    def register_connection(self, connection: ConsoleConnection) -> None:
        LOG.info(f"register console connection from {connection.peer}")
        self._console_client.register_data_listener(connection.write_bytes)
        connection.register_listener(self._console_client.write_bytes)
        self._connections.append(connection)

    def unregister_connection(self, connection: ConsoleConnection) -> None:
        LOG.info(f"unregister console connection from {connection.peer}")
        self._console_client.unregister_data_listener(connection.write_bytes)
        connection.unregister_listener(self._console_client.write_bytes)
        self._connections.remove(connection)

    def exit(self):
        if self._server:
            self._server.close()

    async def wait_exit(self) -> Awaitable[None]:
        if self._server:
            await self._server.wait_closed()
