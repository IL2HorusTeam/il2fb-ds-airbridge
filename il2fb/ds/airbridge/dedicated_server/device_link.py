# coding: utf-8

import asyncio
import logging

from typing import Awaitable, Tuple

from ddict import DotAccessDict
from il2fb.ds.middleware.device_link.client import DeviceLinkClient
from il2fb.ds.middleware.device_link.helpers import (
    decompose_data, compose_answer,
)


LOG = logging.getLogger(__name__)


class DatagramProtocol(asyncio.DatagramProtocol):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        device_link_client: DeviceLinkClient,
    ):
        self._loop = loop
        self._device_link_client = device_link_client

        self._closed_ack = asyncio.Future(loop=self._loop)
        self._transport = None

    def connection_made(self, transport) -> None:
        self._transport = transport

    def connection_lost(self, e: Exception=None) -> None:
        self._closed_ack.set_result(e)

    def wait_closed(self) -> Awaitable[None]:
        return self._closed_ack

    def datagram_received(
        self,
        data: bytes,
        addr: Tuple[str, int],
    ) -> None:
        LOG.debug(f"dat <-- {repr(data)} from {addr}")
        self._loop.create_task(self._execute_request(data, addr))

    async def _execute_request(
        self,
        data: bytes,
        addr: Tuple[str, int],
    ) -> Awaitable[None]:

        try:
            messages = decompose_data(data)
            messages = await self._device_link_client.send_messages(messages)
        except Exception:
            LOG.exception(
                f"failed to execute request {repr(data)} from {addr}"
            )
            return

        if messages:
            try:
                data = compose_answer(messages)
                self._write_bytes(data, addr)
            except Exception:
                LOG.exception(
                    f"failed to respond to {addr} with messages {messages}"
                )

    def _write_bytes(self, data: bytes, addr: Tuple[str, int]) -> None:
        self._transport.sendto(data, addr)
        LOG.debug(f"dat --> {repr(data)} to {addr}")


class DeviceLinkProxy:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        config: DotAccessDict,
        device_link_client: DeviceLinkClient,
    ):
        self._loop = loop
        self._config = config
        self._device_link_client = device_link_client

        self._transport = None
        self._protocol = None

    async def run(self) -> Awaitable[None]:
        loop = self._loop

        address = self._config.bind.address or "localhost"
        port = self._config.bind.port

        self._transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: DatagramProtocol(loop, self._device_link_client),
            local_addr=(address, port),
        )
        await self._protocol.wait_closed()

    def exit(self) -> None:
        if self._transport:
            self._transport.close()

    async def wait_exit(self) -> Awaitable[None]:
        if self._protocol:
            await self._protocol.wait_closed()
