# coding: utf-8

import logging

from il2fb.commons.organization import Belligerents

from il2fb.ds.airbridge import json

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess


LOG = logging.getLogger(__name__)


async def chat_to_all(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

        body = await request.json(loads=json.loads)
        message = body['message']
    except Exception:
        LOG.exception("HTTP failed to chat to all: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].chat_to_all(
            message=message,
            timeout=timeout,
        )
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
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

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
            timeout=timeout,
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
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

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
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to chat to belligerent")
        return RESTInternalServerError(
            detail="failed to chat to belligerent",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)
