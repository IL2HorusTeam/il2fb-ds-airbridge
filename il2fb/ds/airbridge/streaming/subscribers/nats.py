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
            ack_cb=self._handle_ack,
        )

        self._queue = asyncio.Queue(loop=loop)
        self._queue_task = None

        self._is_connected = asyncio.Event(loop=loop)
        self._is_connected.clear()

        self._do_close = False

    @property
    def description(self):
        return (
            f"cluster={self._cluster_id}, subject={self._subject}, "
            f"client={self._client_id}"
        )

    def open(self) -> None:
        coroutine = self._process_queue()
        self._queue_task = self._loop.create_task(coroutine)

    async def wait_opened(self) -> Awaitable[None]:
        await self._client.connect(
            cluster_id=self._cluster_id,
            client_id=self._client_id,
            servers=self._servers,

            allow_reconnect=True,
            max_reconnect_attempts=-1,
            io_loop=self._loop,

            disconnected_cb=self._handle_disconnection,
            reconnected_cb=self._handle_reconnection,
        )
        LOG.info(f"nats connection was established ({self.description})")
        self._is_connected.set()

    def _handle_ack(self, ack):
        LOG.debug(f"nats ack (guid={ack}, {self.description})")

    async def _handle_disconnection(self, *args, **kwargs):
        if self._do_close:
            LOG.info(f"nats connection was closed ({self.description})")
        else:
            self._is_connected.clear()
            LOG.warning(f"nats connection was lost ({self.description})")

    async def _handle_reconnection(self, *args, **kwargs):
        LOG.warning(f"nats connection was restored ({self.description})")
        self._is_connected.set()

    def close(self) -> None:
        self._do_close = True

    async def wait_closed(self) -> Awaitable[None]:
        if self._queue_task:
            self._queue.put_nowait(None)
            await self._queue_task

        if self._client.nc.is_connected and not self._client.nc.is_closed:
            try:
                await self._client.close()
            except Exception:
                LOG.exception(
                    f"failed to close nats connection ({self.description})"
                )

    async def write(self, o: Any) -> Awaitable[None]:
        msg = json.dumps(o).encode()
        await self._queue.put(msg)

    async def _process_queue(self):
        LOG.info(f"nats queue processing was started ({self.description})")

        while True:
            await self._is_connected.wait()

            msg = await self._queue.get()
            if msg is None:
                break

            await self._is_connected.wait()

            try:
                await self._publisher.publish(msg)
            except Exception:
                LOG.exception(
                    f"failed to publish message to nats "
                    f"(msg={msg}, {self.description})"
                )

        LOG.info(f"nats queue processing was stopped ({self.description})")
