# coding: utf-8

import logging

from enum import IntEnum
from typing import Any, Awaitable

from aiohttp import web, WSMsgType

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.api.http.responses.ws import WSSuccess, WSFailure
from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


LOG = logging.getLogger(__name__)


class STREAMING_OPCODE(IntEnum):
    SUBSCRIBE_TO_CHAT = 0
    UNSUBSCRIBE_FROM_CHAT = 1

    SUBSCRIBE_TO_EVENTS = 10
    UNSUBSCRIBE_FROM_EVENTS = 11

    SUBSCRIBE_TO_NOT_PARSED_STRINGS = 20
    UNSUBSCRIBE_FROM_NOT_PARSED_STRINGS = 21

    SUBSCRIBE_TO_RADAR = 30
    UNSUBSCRIBE_FROM_RADAR = 31


class StreamingView(StreamingSubscriber, web.View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._chat_stream = self.request.app['chat_stream']
        self._events_stream = self.request.app['events_stream']
        self._not_parsed_strings_stream = self.request.app['not_parsed_strings_stream']
        self._radar_stream = self.request.app['radar_stream']

        self._ws = None
        self._subscriptions = []

        self._operations = {
            STREAMING_OPCODE.SUBSCRIBE_TO_CHAT: self._subscribe_to_chat,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_CHAT: self._unsubscribe_from_chat,

            STREAMING_OPCODE.SUBSCRIBE_TO_EVENTS: self._subscribe_to_events,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_EVENTS: self._unsubscribe_from_events,

            STREAMING_OPCODE.SUBSCRIBE_TO_NOT_PARSED_STRINGS: self._subscribe_to_not_parsed_strings,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_NOT_PARSED_STRINGS: self._unsubscribe_from_not_parsed_strings,

            STREAMING_OPCODE.SUBSCRIBE_TO_RADAR: self._subscribe_to_radar,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_RADAR: self._unsubscribe_from_radar,
        }

    async def get(self):
        LOG.debug("ws streaming connection was established")

        self._ws = web.WebSocketResponse()
        await self._ws.prepare(self.request)

        async for msg in self._ws:
            if msg.type == WSMsgType.TEXT:
                await self._on_message(msg.data)
            elif msg.type == WSMsgType.ERROR:
                e = self._ws.exception()
                LOG.error(
                    f"ws streaming connection was closed unexpectedly: {e}"
                )

        await self._unsubscribe_from_all()

        LOG.debug("ws streaming connection was closed")
        return self._ws

    async def _on_message(self, message: str) -> Awaitable[None]:
        LOG.debug(f"ws streaming message {repr(message)}")

        if message == "close":
            await self._unsubscribe_from_all()
            await self._ws.close()
        else:
            try:
                data = json.loads(message)
                result = await self._on_data(data)
            except Exception as e:
                LOG.exception(
                    f"failed to handle ws streaming message {repr(message)}"
                )
                await self._ws.send_str(WSFailure(detail=e))
            else:
                await self._ws.send_str(WSSuccess(payload=result))

    async def _on_data(self, data: dict) -> Awaitable[None]:
        opcode = data['opcode']
        LOG.debug(f"ws streaming opcode: {opcode}")

        opcode = STREAMING_OPCODE(opcode)
        operation = self._operations[opcode]

        payload = data.get('payload', {})
        LOG.debug(f"ws streaming payload: {payload}")

        return (await operation(**payload))

    async def _unsubscribe_from_all(self) -> Awaitable[None]:
        subscriptions, self._subscriptions = self._subscriptions, []

        for subscription in subscriptions:
            await subscription.unsubscribe(self)

    async def _subscribe_to_chat(self, **kwargs) -> Awaitable[None]:
        await self._chat_stream.subscribe(self, **kwargs)
        self._subscriptions.append(self._chat_stream)

    async def _unsubscribe_from_chat(self) -> Awaitable[None]:
        await self._chat_stream.unsubscribe(self)
        self._subscriptions.remove(self._chat_stream)

    async def _subscribe_to_events(self, **kwargs) -> Awaitable[None]:
        await self._events_stream.subscribe(self, **kwargs)
        self._subscriptions.append(self._events_stream)

    async def _unsubscribe_from_events(self) -> Awaitable[None]:
        await self._events_stream.unsubscribe(self)
        self._subscriptions.remove(self._events_stream)

    async def _subscribe_to_not_parsed_strings(self, **kwargs) -> Awaitable[None]:
        await self._not_parsed_strings_stream.subscribe(self, **kwargs)
        self._subscriptions.append(self._not_parsed_strings_stream)

    async def _unsubscribe_from_not_parsed_strings(self) -> Awaitable[None]:
        await self._not_parsed_strings_stream.unsubscribe(self)
        self._subscriptions.remove(self._not_parsed_strings_stream)

    async def _subscribe_to_radar(self, **kwargs) -> Awaitable[None]:
        await self._radar_stream.subscribe(self, **kwargs)
        self._subscriptions.append(self._radar_stream)

    async def _unsubscribe_from_radar(self) -> Awaitable[None]:
        await self._radar_stream.unsubscribe(self)
        self._subscriptions.remove(self._radar_stream)

    async def write(self, o: Any) -> Awaitable[None]:
        await self._ws.send_str(json.dumps(o))
