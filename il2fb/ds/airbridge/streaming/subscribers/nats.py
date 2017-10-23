# coding: utf-8

import asyncio
import logging

from typing import Any, Awaitable, List

from nats_stream.aio.client import StreamClient
from nats_stream.aio.publisher import Publisher

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


LOG = logging.getLogger(__name__)


class NATSStreamingSink(StreamingSubscriber):

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        cluster_id: str,
        client_id: str,
        subject: str,
        servers: List[str],
    ):
        super().__init__(loop=loop)

        self._cluster_id = cluster_id
        self._client_id = client_id
        self._subject = subject
        self._servers = servers

        self._client = StreamClient()
        self._publisher = Publisher(
            sc=self._client,
            subject=subject,
            ack_cb=lambda ack: LOG.debug(ack),
        )

    async def write(self, o: Any) -> Awaitable[None]:
        msg = json.dumps(o).encode()
        await self._publisher.publish(msg)

    async def wait_opened(self) -> Awaitable[None]:
        await self._client.connect(
            cluster_id=self._cluster_id,
            client_id=self._client_id,
            servers=self._servers,
            io_loop=self._loop,
        )

    async def wait_closed(self) -> Awaitable[None]:
        if self._client.nc.is_connected and not self._client.nc.is_closed:
            await self._client.close()
