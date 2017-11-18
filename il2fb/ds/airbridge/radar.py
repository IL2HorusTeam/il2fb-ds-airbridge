# coding: utf-8

import logging
import time

from typing import Awaitable, List

from il2fb.commons.structures import BaseStructure

from il2fb.ds.middleware.device_link.client import DeviceLinkClient
from il2fb.ds.middleware.device_link import structures


LOG = logging.getLogger(__name__)


class CompoundActorsPositions(BaseStructure):

    @property
    def is_empty(self):
        return not any((getattr(self, name) for name in self.__slots__))


class AllMovingActorsPositions(CompoundActorsPositions):
    __slots__ = ['aircrafts', 'ground_units', 'ships', ]

    def __init__(
        self,
        aircrafts: List[structures.MovingAircraftPosition],
        ground_units: List[structures.MovingGroundUnitPosition],
        ships: List[structures.ShipPosition],
    ):
        self.aircrafts = aircrafts
        self.ground_units = ground_units
        self.ships = ships


class AllStationaryActorsPositions(CompoundActorsPositions):
    __slots__ = ['stationary_objects', 'houses', 'ships', ]

    def __init__(
        self,
        stationary_objects: List[structures.StationaryObjectPosition],
        houses: List[structures.HousePosition],
        ships: List[structures.ShipPosition],
    ):
        self.stationary_objects = stationary_objects
        self.houses = houses
        self.ships = ships


class Radar:

    def __init__(self, device_link_client: DeviceLinkClient):
        self._client = device_link_client

    async def get_moving_ships_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.ShipPosition]]:

        await self._client.refresh_radar()
        return (await self._get_moving_ships_positions(timeout))

    async def _get_moving_ships_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.ShipPosition]]:

        ships = await self._client.get_all_ships_positions(timeout)
        return [ship for ship in ships if not ship.is_stationary]

    async def get_stationary_ships_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.ShipPosition]]:

        await self._client.refresh_radar()
        return (await self._get_stationary_ships_positions(timeout))

    async def _get_stationary_ships_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.ShipPosition]]:

        ships = await self._client.get_all_ships_positions(timeout)
        return [ship for ship in ships if ship.is_stationary]

    async def get_all_ships_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.ShipPosition]]:

        await self._client.refresh_radar()
        return (await self._client.get_all_ships_positions(timeout))

    async def get_moving_aircrafts_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.MovingAircraftPosition]]:

        await self._client.refresh_radar()
        return (await self._client.get_all_moving_aircrafts_positions(timeout))

    async def get_moving_ground_units_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.MovingGroundUnitPosition]]:

        await self._client.refresh_radar()
        return (await self._client.get_all_moving_ground_units_positions(
            timeout=timeout,
        ))

    async def get_all_moving_actors_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[AllMovingActorsPositions]:

        await self._client.refresh_radar()

        if timeout is None:
            aircrafts = await self._client.get_all_moving_aircrafts_positions()
            ground_units = await self._client.get_all_moving_ground_units_positions()
            ships = await self._get_moving_ships_positions()
        else:
            start_time = time.monotonic()
            aircrafts = await self._client.get_all_moving_aircrafts_positions(
                timeout=timeout,
            )

            end_time = time.monotonic()
            timeout -= (end_time - start_time)
            start_time = end_time
            if timeout <= 0:
                raise TimeoutError

            ground_units = await self._client.get_all_moving_ground_units_positions(
                timeout=timeout,
            )

            end_time = time.monotonic()
            timeout -= (end_time - start_time)
            start_time = end_time
            if timeout <= 0:
                raise TimeoutError

            ships = await self._get_moving_ships_positions(timeout)

        return AllMovingActorsPositions(
            aircrafts=aircrafts,
            ground_units=ground_units,
            ships=ships,
        )

    async def get_stationary_objects_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.StationaryObjectPosition]]:

        await self._client.refresh_radar()
        return (await self._client.get_all_stationary_objects_positions(
            timeout=timeout,
        ))

    async def get_all_houses_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[List[structures.HousePosition]]:

        await self._client.refresh_radar()
        return (await self._client.get_all_houses_positions(timeout))

    async def get_all_stationary_actors_positions(
        self,
        timeout: float=None,
    ) -> Awaitable[AllStationaryActorsPositions]:

        await self._client.refresh_radar()

        if timeout is None:
            stationary_objects = await self._client.get_all_stationary_objects_positions()
            houses = await self._client.get_all_houses_positions()
            ships = await self._get_stationary_ships_positions()
        else:
            start_time = time.monotonic()
            stationary_objects = await self._client.get_all_stationary_objects_positions(
                timeout=timeout,
            )

            end_time = time.monotonic()
            timeout -= (end_time - start_time)
            start_time = end_time
            if timeout <= 0:
                raise TimeoutError

            houses = await self._client.get_all_houses_positions(timeout)

            end_time = time.monotonic()
            timeout -= (end_time - start_time)
            start_time = end_time
            if timeout <= 0:
                raise TimeoutError

            ships = await self._get_stationary_ships_positions(timeout)

        return AllStationaryActorsPositions(
            stationary_objects=stationary_objects,
            houses=houses,
            ships=ships,
        )
