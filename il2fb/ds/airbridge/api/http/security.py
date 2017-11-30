# coding: utf-8

import base64
import functools
import logging

from typing import Optional

import aiohttp_cors

from aiohttp import web

from il2fb.ds.airbridge.api.http.constants import DEFAULT_AUTH_TOKEN_HEADER_NAME
from il2fb.ds.airbridge.typing import StringOrPath


LOG = logging.getLogger(__name__)


def setup_cors(app: web.Application, options: dict) -> None:
    defaults = {
        key: aiohttp_cors.ResourceOptions(**value)
        for key, value in options.items()
    }
    cors = aiohttp_cors.setup(app, defaults=defaults)

    for route in app.router.routes():
        cors.add(route)


class AuthorizationBackend:

    def __init__(
        self,
        token_storage_path: StringOrPath,
        token_header_name: Optional[str]=None,
    ):
        self._token_header_name = (
            token_header_name or DEFAULT_AUTH_TOKEN_HEADER_NAME
        )

        with open(token_storage_path, 'r') as f:
            tokens = f.readlines()
            tokens = map(str.strip, tokens)
            tokens = filter(bool, tokens)
            tokens = map(base64.b64decode, tokens)
            self._token_storage = set(tokens)

    def authorize(self, request: web.Request) -> bool:
        try:
            token = request.headers.get(self._token_header_name)
            if not token:
                return False

            token = base64.b64decode(token)
            return token in self._token_storage
        except Exception:
            LOG.exception("failed to perform request authorization")
            return False


def setup_authorization(
    app: web.Application,
    authorization_backend: AuthorizationBackend,
) -> None:
    app['auth_backend'] = authorization_backend


def with_authorization(view):

    @functools.wraps(view)
    async def wrapper(arg0, *args, **kwargs):
        request = arg0 if isinstance(arg0, web.Request) else arg0.request
        backend = request.app.get('auth_backend')

        if backend and not backend.authorize(request):
            raise web.HTTPForbidden()

        return (await view(arg0, *args, **kwargs))

    return wrapper
