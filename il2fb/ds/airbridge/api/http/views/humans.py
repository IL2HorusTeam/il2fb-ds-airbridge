# coding: utf-8

import logging

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess


LOG = logging.getLogger(__name__)


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
