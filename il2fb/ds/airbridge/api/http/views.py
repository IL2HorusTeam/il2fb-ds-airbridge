# coding: utf-8

import logging

from il2fb.commons.organization import Belligerents

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess


LOG = logging.getLogger(__name__)


async def get_health(request):
    pretty = 'pretty' in request.query
    payload = {'status': 'alive'}

    return RESTSuccess(payload=payload, pretty=pretty)


async def get_server_info(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['console_client'].get_server_info()
    except Exception:
        LOG.exception("HTTP failed to get server info")
        return RESTInternalServerError(
            detail="failed to get server info",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_humans_list(request):
    pretty = 'pretty' in request.query

    try:
        items = await request.app['console_client'].get_humans_list()
    except Exception:
        LOG.exception("HTTP failed to get humans list")
        return RESTInternalServerError(
            detail="failed to get humans list",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=items, pretty=pretty)


async def get_humans_count(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['console_client'].get_humans_count()
    except Exception:
        LOG.exception("HTTP failed to get humans count")
        return RESTInternalServerError(
            detail="failed to get humans count",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def get_humans_statistics(request):
    pretty = 'pretty' in request.query

    try:
        items = await request.app['console_client'].get_humans_statistics()
    except Exception:
        LOG.exception("HTTP failed to get humans statistics")
        return RESTInternalServerError(
            detail="failed to get humans statistics",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=items, pretty=pretty)


async def kick_all_humans(request):
    pretty = 'pretty' in request.query

    try:
        await request.app['console_client'].kick_all_humans()
    except Exception:
        LOG.exception("HTTP failed to kick all humans")
        return RESTInternalServerError(
            detail="failed to kick all humans",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def kick_human_by_callsign(request):
    pretty = 'pretty' in request.query

    try:
        callsign = request.match_info['callsign']
    except Exception:
        LOG.exception(
            "HTTP failed to kick human by callsign: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].kick_human_by_callsign(callsign)
    except Exception:
        LOG.exception("HTTP failed to kick human by callsign")
        return RESTInternalServerError(
            detail="failed to kick human by callsign",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def chat_to_all(request):
    pretty = 'pretty' in request.query

    try:
        body = await request.json(loads=json.loads)
        message = body['message']
    except Exception:
        LOG.exception("HTTP failed to chat to all: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].chat_to_all(message)
    except Exception:
        LOG.exception("HTTP failed to chat to all")
        return RESTInternalServerError(
            detail="failed to chat to all",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def chat_to_human(request):
    pretty = 'pretty' in request.query

    try:
        callsign = request.match_info['callsign']
        body = await request.json(loads=json.loads)
        message = body['message']
    except Exception:
        LOG.exception("HTTP failed to chat to human: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].chat_to_human(
            message=message,
            addressee=callsign,
        )
    except Exception:
        LOG.exception("HTTP failed to chat to human")
        return RESTInternalServerError(
            detail="failed to chat to human",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def chat_to_belligerent(request):
    pretty = 'pretty' in request.query

    try:
        belligerent = request.match_info['belligerent']
        belligerent = int(belligerent)
        belligerent = Belligerents.get_by_value(belligerent)
        body = await request.json(loads=json.loads)
        message = body['message']
    except Exception:
        LOG.exception(
            "HTTP failed to chat to belligerent: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].chat_to_belligerent(
            message=message,
            addressee=belligerent,
        )
    except Exception:
        LOG.exception("HTTP failed to chat to belligerent")
        return RESTInternalServerError(
            detail="failed to chat to belligerent",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def load_mission(request):
    pretty = 'pretty' in request.query

    try:
        body = await request.json(loads=json.loads)
        file_path = body['file_path']
    except Exception:
        LOG.exception("HTTP failed to load mission: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].load_mission(file_path)
    except Exception:
        LOG.exception("HTTP failed to load mission")
        return RESTInternalServerError(
            detail="failed to load mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def get_current_mission_info(request):
    pretty = 'pretty' in request.query

    try:
        result = await request.app['console_client'].get_mission_info()
    except Exception:
        LOG.exception("HTTP failed to get current mission info")
        return RESTInternalServerError(
            detail="failed to get current mission info",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


async def begin_current_mission(request):
    pretty = 'pretty' in request.query

    try:
        await request.app['console_client'].begin_mission()
    except Exception:
        LOG.exception("HTTP failed to begin current mission")
        return RESTInternalServerError(
            detail="failed to begin current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def end_current_mission(request):
    pretty = 'pretty' in request.query

    try:
        await request.app['console_client'].end_mission()
    except Exception:
        LOG.exception("HTTP failed to end current mission")
        return RESTInternalServerError(
            detail="failed to end current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


async def unload_current_mission(request):
    pretty = 'pretty' in request.query

    try:
        await request.app['console_client'].unload_mission()
    except Exception:
        LOG.exception("HTTP failed to unload current mission")
        return RESTInternalServerError(
            detail="failed to unload current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


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
