# coding: utf-8

import asyncio

from typing import Optional

from aiohttp import web

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.airbridge.radar import Radar

from il2fb.ds.airbridge.streaming.facilities import ChatStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import EventsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import NotParsedStringsStreamingFacility

from il2fb.ds.airbridge.api.http.constants import ACCESS_LOG_FORMAT
from il2fb.ds.airbridge.api.http.routes import setup_routes
from il2fb.ds.airbridge.api.http.security import setup_cors


def build_http_api(
    loop: asyncio.AbstractEventLoop,
    console_client: ConsoleClient,
    radar: Radar,
    chat: ChatStreamingFacility,
    events: EventsStreamingFacility,
    not_parsed_strings: NotParsedStringsStreamingFacility,
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
    app['console_client'] = console_client
    app['radar'] = radar
    app['chat'] = chat
    app['events'] = events
    app['not_parsed_strings'] = not_parsed_strings

    setup_routes(app)
    setup_cors(app)

    return app
