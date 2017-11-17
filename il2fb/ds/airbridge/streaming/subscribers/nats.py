# coding: utf-8

import asyncio
import logging

from typing import Any, Awaitable

from nats_stream.aio.publisher import Publisher

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.streaming.subscribers.base import PluggableStreamingSubscriber


LOG = logging.getLogger(__name__)


class NATSStreamingSink(PluggableStreamingSubscriber):

    def __init__(self, app, subject: str):
        super().__init__(app=app)

        self._subject = subject
        self._queue = asyncio.Queue(loop=app.loop)
        self._queue_task = None

    def plug_in(self) -> None:
        self._client = self._app.nats_streaming_client
        self._publisher = Publisher(
            sc=self._client,
            subject=self._subject,
            ack_cb=self._handle_ack,
        )

        queue_coroutine = self._process_queue()
        self._queue_task = self._app.loop.create_task(queue_coroutine)

    def _handle_ack(self, ack) -> None:
        LOG.debug(f"nats streaming ack (guid={ack}, subject={self._subject})")

    def unplug(self) -> None:
        if self._queue_task:
            self._queue.put_nowait(None)

    async def wait_unplugged(self) -> Awaitable[None]:
        if self._queue_task:
            await self._queue_task

    async def write(self, o: Any) -> Awaitable[None]:
        msg = json.dumps(o).encode()
        await self._queue.put(msg)

    async def _process_queue(self) -> Awaitable[None]:
        LOG.info(
            f"processing of nats streaming queue was started "
            f"(subject={self._subject})"
        )

        while True:
            await self._client.connection_event.wait()

            msg = await self._queue.get()
            if msg is None:
                break

            await self._client.connection_event.wait()

            try:
                await self._publisher.publish(msg)
            except Exception:
                LOG.exception(
                    f"failed to publish message to nats "
                    f"(msg={msg}, {self.description})"
                )

        LOG.info(
            f"processing of nats streaming queue was stopped "
            f"(subject={self._subject})"
        )
