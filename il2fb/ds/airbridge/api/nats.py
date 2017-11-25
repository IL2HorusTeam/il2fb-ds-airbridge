# coding: utf-8

import logging

from enum import IntEnum

from typing import Awaitable, Optional, Any

from nats.aio.client import Msg

from il2fb.commons.organization import Belligerents
from il2fb.ds.middleware.console.client import ConsoleClient

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.nats import NATSClient
from il2fb.ds.airbridge.radar import Radar


LOG = logging.getLogger(__name__)


class NATS_OPCODE(IntEnum):
    GET_SERVER_INFO = 0

    GET_HUMANS_LIST = 10
    GET_HUMANS_COUNT = 11
    GET_HUMANS_STATISTICS = 12

    KICK_ALL_HUMANS = 20
    KICK_HUMAN_BY_CALLSIGN = 21

    CHAT_TO_ALL = 30
    CHAT_TO_HUMAN = 31
    CHAT_TO_BELLIGERENT = 32

    GET_MISSION_INFO = 40
    LOAD_MISSION = 41
    BEGIN_MISSION = 42
    END_MISSION = 43
    UNLOAD_MISSION = 44

    GET_ALL_SHIPS_POSITIONS = 50
    GET_MOVING_SHIPS_POSITIONS = 51
    GET_STATIONARY_SHIPS_POSITIONS = 52

    GET_MOVING_AIRCRAFTS_POSITIONS = 53
    GET_MOVING_GROUND_UNITS_POSITIONS = 54
    GET_ALL_MOVING_ACTORS_POSITIONS = 55

    GET_ALL_HOUSES_POSITIONS = 56
    GET_STATIONARY_OBJECTS_POSITIONS = 57
    GET_ALL_STATIONARY_ACTORS_POSITIONS = 58


class NATS_STATUS(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class NATSSubscriber:

    def __init__(
        self,
        nats_client: NATSClient,
        subject: str,
        console_client: ConsoleClient,
        radar: Radar,
        trace=False,
    ):
        self._nats_client = nats_client
        self._subject = subject
        self._console_client = console_client
        self._radar = radar
        self._trace = trace

        self._ssid = None
        self._operations = {
            NATS_OPCODE.GET_SERVER_INFO: self._console_client.get_server_info,

            NATS_OPCODE.GET_HUMANS_LIST: self._console_client.get_humans_list,
            NATS_OPCODE.GET_HUMANS_COUNT: self._console_client.get_humans_count,
            NATS_OPCODE.GET_HUMANS_STATISTICS: self._console_client.get_humans_statistics,

            NATS_OPCODE.KICK_ALL_HUMANS: self._console_client.kick_all_humans,
            NATS_OPCODE.KICK_HUMAN_BY_CALLSIGN: self._console_client.kick_human_by_callsign,

            NATS_OPCODE.CHAT_TO_ALL: self._console_client.chat_to_all,
            NATS_OPCODE.CHAT_TO_HUMAN: self._console_client.chat_to_human,
            NATS_OPCODE.CHAT_TO_BELLIGERENT: self._chat_to_belligerent,

            NATS_OPCODE.GET_MISSION_INFO: self._console_client.get_mission_info,
            NATS_OPCODE.LOAD_MISSION: self._console_client.load_mission,
            NATS_OPCODE.BEGIN_MISSION: self._console_client.begin_mission,
            NATS_OPCODE.END_MISSION: self._console_client.end_mission,
            NATS_OPCODE.UNLOAD_MISSION: self._console_client.unload_mission,

            NATS_OPCODE.GET_ALL_SHIPS_POSITIONS: self._radar.get_all_ships_positions,
            NATS_OPCODE.GET_MOVING_SHIPS_POSITIONS: self._radar.get_moving_ships_positions,
            NATS_OPCODE.GET_STATIONARY_SHIPS_POSITIONS: self._radar.get_stationary_ships_positions,

            NATS_OPCODE.GET_MOVING_AIRCRAFTS_POSITIONS: self._radar.get_moving_aircrafts_positions,
            NATS_OPCODE.GET_MOVING_GROUND_UNITS_POSITIONS: self._radar.get_moving_ground_units_positions,
            NATS_OPCODE.GET_ALL_MOVING_ACTORS_POSITIONS: self._radar.get_all_moving_actors_positions,

            NATS_OPCODE.GET_ALL_HOUSES_POSITIONS: self._radar.get_all_houses_positions,
            NATS_OPCODE.GET_STATIONARY_OBJECTS_POSITIONS: self._radar.get_stationary_objects_positions,
            NATS_OPCODE.GET_ALL_STATIONARY_ACTORS_POSITIONS: self._radar.get_all_stationary_actors_positions,
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
                details=(str(e) or e.__class__.__name__),
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

    async def _chat_to_belligerent(
        self,
        message: str,
        addressee: int,
    ) -> Awaitable[None]:

        addressee = Belligerents.get_by_value(addressee)
        await self._console_client.chat_to_belligerent(message, addressee)
