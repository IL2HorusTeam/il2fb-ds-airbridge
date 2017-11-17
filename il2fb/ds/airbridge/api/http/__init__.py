# coding: utf-8

import asyncio

from typing import Optional

from aiohttp import web

from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.parsers.mission import MissionParser

from il2fb.ds.airbridge.dedicated_server.instance import DedicatedServer
from il2fb.ds.airbridge.radar import Radar

from il2fb.ds.airbridge.streaming.facilities import ChatStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import EventsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import NotParsedStringsStreamingFacility
from il2fb.ds.airbridge.streaming.facilities import RadarStreamingFacility

from il2fb.ds.airbridge.api.http.constants import ACCESS_LOG_FORMAT
from il2fb.ds.airbridge.api.http.routes import setup_routes
from il2fb.ds.airbridge.api.http.security import setup_cors


def build_http_api(
    loop: asyncio.AbstractEventLoop,
    dedicated_server: DedicatedServer,
    console_client: ConsoleClient,
    radar: Radar,
    chat: ChatStreamingFacility,
    events: EventsStreamingFacility,
    not_parsed_strings: NotParsedStringsStreamingFacility,
    radar_stream: RadarStreamingFacility,
    mission_parser: MissionParser,
    config: Optional[dict]=None,
    **kwargs
):

    app = web.Application(
        loop=loop,
        handler_args=dict(
            access_log_format=ACCESS_LOG_FORMAT,
        ),
        **kwargs,
    )

    app['dedicated_server'] = dedicated_server
    app['console_client'] = console_client
    app['radar'] = radar
    app['mission_parser'] = mission_parser
    app['config'] = config if config is not None else {}

    app['chat'] = chat
    app['events'] = events
    app['not_parsed_strings'] = not_parsed_strings
    app['radar_stream'] = radar_stream

    setup_routes(app.router)
    setup_cors(app)

    return app
