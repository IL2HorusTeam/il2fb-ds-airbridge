# coding: utf-8

import logging

from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess


LOG = logging.getLogger(__name__)


async def get_all_ships_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_all_ships_positions()
    except Exception:
        LOG.exception("HTTP failed to get all ships positions")
        return RESTInternalServerError(
            detail="failed to get all ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_moving_ships_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_moving_ships_positions()
    except Exception:
        LOG.exception("HTTP failed to get moving ships positions")
        return RESTInternalServerError(
            detail="failed to get moving ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_stationary_ships_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_stationary_ships_positions()
    except Exception:
        LOG.exception("HTTP failed to get stationary ships positions")
        return RESTInternalServerError(
            detail="failed to get stationary ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_moving_aircrafts_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_moving_aircrafts_positions()
    except Exception:
        LOG.exception("HTTP failed to get moving aircrafts positions")
        return RESTInternalServerError(
            detail="failed to get moving aircrafts positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_moving_ground_units_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_moving_ground_units_positions()
    except Exception:
        LOG.exception("HTTP failed to get moving ground units positions")
        return RESTInternalServerError(
            detail="failed to get moving ground units positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_all_houses_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_all_houses_positions()
    except Exception:
        LOG.exception("HTTP failed to get all houses positions")
        return RESTInternalServerError(
            detail="failed to get all houses positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_stationary_objects_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_stationary_objects_positions()
    except Exception:
        LOG.exception("HTTP failed to get stationary objects positions")
        return RESTInternalServerError(
            detail="failed to get stationary objects positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_all_moving_actors_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_all_moving_actors_positions()
    except Exception:
        LOG.exception("HTTP failed to get all moving actors positions")
        return RESTInternalServerError(
            detail="failed to get all moving actors positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_all_stationary_actors_positions(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['radar'].get_all_stationary_actors_positions()
    except Exception:
        LOG.exception("HTTP failed to get all stationary actors positions")
        return RESTInternalServerError(
            detail="failed to get all stationary actors positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)
