# coding: utf-8

import logging

from il2fb.commons.organization import Belligerents

from il2fb.ds.airbridge import json

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess
from il2fb.ds.airbridge.api.http.security import with_authorization


LOG = logging.getLogger(__name__)


@with_authorization
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


@with_authorization
async def chat_to_human(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

        addressee = request.match_info['addressee']
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
            addressee=addressee,
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


@with_authorization
async def chat_to_belligerent(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

        addressee = request.match_info['addressee']
        addressee = int(addressee)
        addressee = Belligerents.get_by_value(addressee)

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
            addressee=addressee,
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
