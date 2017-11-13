# coding: utf-8

from .responses.rest import RESTSuccess


async def http_health(request):
    pretty = 'pretty' in request.query
    return RESTSuccess(payload={'status': 'alive'}, pretty=pretty)
