# coding: utf-8

import logging

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
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception("HTTP failed to get server info: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['console_client'].get_server_info(timeout)
    except Exception:
        LOG.exception("HTTP failed to get server info")
        return RESTInternalServerError(
            detail="failed to get server info",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)
