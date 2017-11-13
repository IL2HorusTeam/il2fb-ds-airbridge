# coding: utf-8

import asyncio

from typing import Optional

from aiohttp import web

from .constants import ACCESS_LOG_FORMAT
from .routes import setup_routes
from .security import setup_cors


def build_http_api(
    loop: asyncio.AbstractEventLoop,
    config: Optional[dict]=None,
    **kwargs
):
    if config is None:
        config = {}

    app = web.Application(
        loop=loop,
        handler_args=dict(
            access_log_format=ACCESS_LOG_FORMAT,
        ),
        **kwargs,
    )
    app['config'] = config

    setup_routes(app)
    setup_cors(app)

    return app
