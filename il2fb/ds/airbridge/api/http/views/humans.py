# coding: utf-8

import logging

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess
from il2fb.ds.airbridge.api.http.security import with_authorization


LOG = logging.getLogger(__name__)


@with_authorization
async def get_humans_list(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception("HTTP failed to get humans list: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        items = await request.app['console_client'].get_humans_list(timeout)
    except Exception:
        LOG.exception("HTTP failed to get humans list")
        return RESTInternalServerError(
            detail="failed to get humans list",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=items, pretty=pretty)


@with_authorization
async def get_humans_count(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception("HTTP failed to get humans count: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['console_client'].get_humans_count(timeout)
    except Exception:
        LOG.exception("HTTP failed to get humans count")
        return RESTInternalServerError(
            detail="failed to get humans count",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_humans_statistics(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get humans statistics: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        items = await request.app['console_client'].get_humans_statistics(
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to get humans statistics")
        return RESTInternalServerError(
            detail="failed to get humans statistics",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=items, pretty=pretty)


@with_authorization
async def kick_all_humans(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception("HTTP failed to kick all humans: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].kick_all_humans(timeout)
    except Exception:
        LOG.exception("HTTP failed to kick all humans")
        return RESTInternalServerError(
            detail="failed to kick all humans",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def kick_human_by_callsign(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

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
        await request.app['console_client'].kick_human_by_callsign(
            callsign=callsign,
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to kick human by callsign")
        return RESTInternalServerError(
            detail="failed to kick human by callsign",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)
