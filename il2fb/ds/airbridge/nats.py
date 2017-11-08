# coding: utf-8

import asyncio
import logging

from typing import Awaitable, List

from nats.aio.client import (
    Client, DEFAULT_RECONNECT_TIME_WAIT, DEFAULT_PING_INTERVAL,
    DEFAULT_MAX_OUTSTANDING_PINGS, DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
)
from nats_stream.aio.client import StreamClient, DEFAULT_CONNECT_WAIT


LOG = logging.getLogger(__name__)


class NATSClient(Client):

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()

        self._loop = loop
        self._do_close = False

        self._connection_event = asyncio.Event(loop=loop)
        self._connection_event.clear()

    @property
    def connection_event(self) -> asyncio.Event:
        return self._connection_event

    async def connect(
        self,
        servers: List[str],
        name: str=None,
        pedantic: bool=False,
        verbose: bool=False,
        reconnect_time_wait: int=DEFAULT_RECONNECT_TIME_WAIT,
        ping_interval: int=DEFAULT_PING_INTERVAL,
        max_outstanding_pings: int=DEFAULT_MAX_OUTSTANDING_PINGS,
        dont_randomize: bool=False,
        flusher_queue_size: int=DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
    ) -> Awaitable[None]:

        await super().connect(
            io_loop=self._loop,
            servers=servers,

            name=name,
            pedantic=pedantic,
            verbose=verbose,

            allow_reconnect=True,
            max_reconnect_attempts=-1,
            reconnect_time_wait=reconnect_time_wait,

            ping_interval=ping_interval,
            max_outstanding_pings=max_outstanding_pings,
            dont_randomize=dont_randomize,
            flusher_queue_size=flusher_queue_size,

            disconnected_cb=self._handle_disconnection,
            reconnected_cb=self._handle_reconnection,
        )
        LOG.info(
            f"nats connection was established "
            f"(url={self.connected_url.netloc})"
        )
        self._connection_event.set()

    async def _handle_disconnection(self, *args, **kwargs) -> Awaitable[None]:
        self._connection_event.clear()

        if self._do_close:
            LOG.info("nats connection was closed")
        else:
            LOG.warning("nats connection was lost")

    async def _handle_reconnection(self, *args, **kwargs) -> Awaitable[None]:
        LOG.info(
            f"nats connection was reestablished "
            f"(url={self.connected_url.netloc})"
        )
        self._connection_event.set()

    async def close(self) -> None:
        self._do_close = True
        await super().close()


class NATSStreamingClient(StreamClient):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        nats_client: NATSClient,
    ):
        super().__init__()

        self._loop = loop
        self.nc = nats_client

    @property
    def connection_event(self) -> asyncio.Event:
        return self.nc.connection_event

    async def connect(
        self,
        cluster_id: str,
        client_id: str,
        connect_timeout: int=DEFAULT_CONNECT_WAIT,
        verbose: bool=False,
        **options
    ) -> Awaitable[None]:

        await super().connect(
            cluster_id=cluster_id,
            client_id=client_id,
            nc=self.nc,
            connect_timeout=connect_timeout,
            io_loop=self._loop,
            verbose=verbose,
            **options
        )
