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

        self._data_subscribers = []

    @property
    def peer(self):
        return self._peer

    def subscribe_to_data(self, subscriber: Callable[[bytes], None]) -> None:
        """
        Not thread-safe.

        """
        self._data_subscribers.append(subscriber)

    def unsubscribe_from_data(self, subscriber: Callable[[bytes], None]) -> None:
        """
        Not thread-safe.

        """
        self._data_subscribers.remove(subscriber)

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

        for subscriber in self._data_subscribers:
            try:
                subscriber(data)
            except Exception:
                LOG.exception(
                    f"failed to send data {repr(data)} to subscriber "
                    f"{subscriber}"
                )

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

    async def run(self) -> Awaitable[None]:
        self._server = await self._loop.create_server(
            lambda: ConsoleConnection(loop=self._loop, registry=self),
            (self._config.bind.address or "localhost"),
            self._config.bind.port,
        )
        await self._server.wait_closed()

    def register_connection(self, connection: ConsoleConnection) -> None:
        LOG.info(f"subscribe console connection to {connection.peer}")

        self._console_client.subscribe_to_data(connection.write_bytes)
        connection.subscribe_to_data(self._console_client.write_bytes)

        self._connections.append(connection)

    def unregister_connection(self, connection: ConsoleConnection) -> None:
        LOG.info(f"unsubscribe console connection from {connection.peer}")

        self._console_client.unsubscribe_from_data(connection.write_bytes)
        connection.unsubscribe_from_data(self._console_client.write_bytes)

        self._connections.remove(connection)

    def exit(self) -> None:
        if self._server:
            self._server.close()

    async def wait_exit(self) -> Awaitable[None]:
        if self._server:
            await self._server.wait_closed()
