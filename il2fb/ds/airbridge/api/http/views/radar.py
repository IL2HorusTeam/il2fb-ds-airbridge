# coding: utf-8

import logging

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess
from il2fb.ds.airbridge.api.http.security import with_authorization


LOG = logging.getLogger(__name__)


@with_authorization
async def get_all_ships_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get all ships positions: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_all_ships_positions(timeout)
    except Exception:
        LOG.exception("HTTP failed to get all ships positions")
        return RESTInternalServerError(
            detail="failed to get all ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_moving_ships_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get moving ships positions: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_moving_ships_positions(timeout)
    except Exception:
        LOG.exception("HTTP failed to get moving ships positions")
        return RESTInternalServerError(
            detail="failed to get moving ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_stationary_ships_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get stationary ships positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_stationary_ships_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get stationary ships positions")
        return RESTInternalServerError(
            detail="failed to get stationary ships positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_moving_aircrafts_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get moving aircrafts positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_moving_aircrafts_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get moving aircrafts positions")
        return RESTInternalServerError(
            detail="failed to get moving aircrafts positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_moving_ground_units_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get moving ground units positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_moving_ground_units_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get moving ground units positions")
        return RESTInternalServerError(
            detail="failed to get moving ground units positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_all_houses_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get all houses positions: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_all_houses_positions(timeout)
    except Exception:
        LOG.exception("HTTP failed to get all houses positions")
        return RESTInternalServerError(
            detail="failed to get all houses positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_stationary_objects_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get stationary objects positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_stationary_objects_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get stationary objects positions")
        return RESTInternalServerError(
            detail="failed to get stationary objects positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_all_moving_actors_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get all moving actors positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_all_moving_actors_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get all moving actors positions")
        return RESTInternalServerError(
            detail="failed to get all moving actors positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_all_stationary_actors_positions(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get all stationary actors positions: "
            "incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['radar'].get_all_stationary_actors_positions(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get all stationary actors positions")
        return RESTInternalServerError(
            detail="failed to get all stationary actors positions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)
