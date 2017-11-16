# coding: utf-8

import logging

from enum import IntEnum

from aiohttp import web, WSMsgType

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.api.http.responses.ws import WSSuccess, WSFailure


LOG = logging.getLogger(__name__)


class STREAMING_OPCODE(IntEnum):
    SUBSCRIBE_TO_CHAT = 0
    UNSUBSCRIBE_FROM_CHAT = 1

    SUBSCRIBE_TO_EVENTS = 10
    UNSUBSCRIBE_FROM_EVENTS = 11

    SUBSCRIBE_TO_NOT_PARSED_STRINGS = 20
    UNSUBSCRIBE_FROM_NOT_PARSED_STRINGS = 21


class StreamingView(web.View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._chat = self.request.app['chat']
        self._events = self.request.app['events']
        self._not_parsed_strings = self.request.app['not_parsed_strings']

        self._ws = None
        self._subscriptions = []

        self._operations = {
            STREAMING_OPCODE.SUBSCRIBE_TO_CHAT: self._subscribe_to_chat,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_CHAT: self._unsubscribe_from_chat,

            STREAMING_OPCODE.SUBSCRIBE_TO_EVENTS: self._subscribe_to_events,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_EVENTS: self._unsubscribe_from_events,

            STREAMING_OPCODE.SUBSCRIBE_TO_NOT_PARSED_STRINGS: self._subscribe_to_not_parsed_strings,
            STREAMING_OPCODE.UNSUBSCRIBE_FROM_NOT_PARSED_STRINGS: self._unsubscribe_from_not_parsed_strings,
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

    async def _on_message(self, message):
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

    async def _on_data(self, data):
        opcode = data['opcode']
        LOG.debug(f"ws streaming opcode: {opcode}")

        opcode = STREAMING_OPCODE(opcode)
        operation = self._operations[opcode]

        payload = data.get('payload', {})
        LOG.debug(f"ws streaming payload: {payload}")

        return (await operation(**payload))

    async def _unsubscribe_from_all(self):
        subscriptions, self._subscriptions = self._subscriptions, []

        for subscription in subscriptions:
            await subscription.unsubscribe(self._write_data)

    async def _subscribe_to_chat(self, **kwargs):
        await self._chat.subscribe(self._write_data, **kwargs)
        self._subscriptions.append(self._chat)

    async def _unsubscribe_from_chat(self):
        await self._chat.unsubscribe(self._write_data)
        self._subscriptions.remove(self._chat)

    async def _subscribe_to_events(self, **kwargs):
        await self._events.subscribe(self._write_data, **kwargs)
        self._subscriptions.append(self._events)

    async def _unsubscribe_from_events(self):
        await self._events.unsubscribe(self._write_data)
        self._subscriptions.remove(self._events)

    async def _subscribe_to_not_parsed_strings(self, **kwargs):
        await self._not_parsed_strings.subscribe(self._write_data, **kwargs)
        self._subscriptions.append(self._not_parsed_strings)

    async def _unsubscribe_from_not_parsed_strings(self):
        await self._not_parsed_strings.unsubscribe(self._write_data)
        self._subscriptions.remove(self._not_parsed_strings)

    async def _write_data(self, o):
        await self._ws.send_str(json.dumps(o))
