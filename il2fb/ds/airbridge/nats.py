# coding: utf-8

import asyncio
import logging

from enum import IntEnum
from typing import Awaitable, List, Optional, Any

from nats.aio.client import Client
from nats.aio.client import DEFAULT_MAX_FLUSHER_QUEUE_SIZE
from nats.aio.client import DEFAULT_MAX_OUTSTANDING_PINGS
from nats.aio.client import DEFAULT_RECONNECT_TIME_WAIT
from nats.aio.client import DEFAULT_PING_INTERVAL
from nats.aio.client import Msg

from nats_stream.aio.client import DEFAULT_CONNECT_WAIT
from nats_stream.aio.client import StreamClient

from il2fb.ds.middleware.console.client import ConsoleClient

from il2fb.ds.airbridge import json


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


class NATS_OPCODE(IntEnum):
    SERVER_INFO = 0

    USER_LIST = 10
    USER_STATS = 11
    USER_COUNT = 12

    MISSION_STATUS = 20
    MISSION_LOAD = 21
    MISSION_UNLOAD = 22
    MISSION_BEGIN = 23
    MISSION_END = 24

    KICK_BY_CALLSIGN = 30
    KICK_BY_NUMBER = 31
    KICK_ALL = 32

    CHAT_ALL = 40
    CHAT_USER = 41
    CHAT_BELLIGERENT = 42


class NATS_STATUS(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class NATSSubscriber:

    def __init__(
        self,
        nats_client: NATSClient,
        subject: str,
        console_client: ConsoleClient,
        trace=False,
    ):
        self._nats_client = nats_client
        self._subject = subject
        self._console_client = console_client
        self._trace = trace
        self._ssid = None
        self._operations = {
            NATS_OPCODE.SERVER_INFO: self._console_client.server_info,
            NATS_OPCODE.USER_LIST: self._console_client.user_list,
            NATS_OPCODE.USER_STATS: self._console_client.user_stats,
            NATS_OPCODE.USER_COUNT: self._console_client.user_count,
            NATS_OPCODE.MISSION_STATUS: self._console_client.mission_status,
            NATS_OPCODE.MISSION_LOAD: self._console_client.mission_load,
            NATS_OPCODE.MISSION_UNLOAD: self._console_client.mission_unload,
            NATS_OPCODE.MISSION_BEGIN: self._console_client.mission_begin,
            NATS_OPCODE.MISSION_END: self._console_client.mission_end,
            NATS_OPCODE.KICK_BY_CALLSIGN: self._console_client.kick_by_callsign,
            NATS_OPCODE.KICK_BY_NUMBER: self._console_client.kick_by_number,
            NATS_OPCODE.KICK_ALL: self._console_client.kick_all,
            NATS_OPCODE.CHAT_ALL: self._console_client.chat_all,
            NATS_OPCODE.CHAT_USER: self._console_client.chat_user,
            NATS_OPCODE.CHAT_BELLIGERENT: self._console_client.chat_belligerent,
        }

    async def start(self) -> Awaitable[None]:
        self._ssid = await self._nats_client.subscribe(
            subject=self._subject,
            cb=self._try_handle_request,
        )
        LOG.info(f"subscribed to nats subject '{self._subject}'")

    async def stop(self) -> Awaitable[None]:
        await self._nats_client.unsubscribe(
            ssid=self._ssid,
        )
        LOG.info(f"unsubscribed from nats subject '{self._subject}'")

    async def _try_handle_request(self, request: Msg) -> Awaitable[None]:
        LOG.debug(
            f"nats request (data={request.data}, subscriber='{request.reply}')"
        )

        try:
            result = await self._handle_message(request.data)
        except Exception as e:
            LOG.exception(
                f"failed to handle nats request (data={request.data})"
            )
            response = dict(
                status=NATS_STATUS.FAILURE,
                payload=str(e),
            )
        else:
            response = dict(
                status=NATS_STATUS.SUCCESS,
                payload=result,
            )

        if request.reply:
            try:
                data = json.dumps(response)
                data = data.encode()
                await self._nats_client.publish(request.reply, data)
            except Exception:
                LOG.exception(
                    f"failed to publish nats response (data={response})"
                )
            else:
                LOG.debug(
                    f"nats response (data={data})"
                )

    async def _handle_message(self, msg: bytes) -> Awaitable[Optional[Any]]:
        msg = msg.decode()
        msg = json.loads(msg)

        opcode = msg['opcode']

        if self._trace:
            LOG.debug(f"nats opcode: {opcode}")

        opcode = NATS_OPCODE(opcode)
        operation = self._operations[opcode]

        if self._trace:
            LOG.debug(f"nats operation: {operation.__name__}")

        payload = msg.get('payload', {})

        if self._trace:
            LOG.debug(f"nats payload: {payload}")

        result = await operation(**payload)

        if self._trace:
            LOG.debug(f"nats result: {result}")

        return result
