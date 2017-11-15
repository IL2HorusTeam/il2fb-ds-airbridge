# coding: utf-8

import logging

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
