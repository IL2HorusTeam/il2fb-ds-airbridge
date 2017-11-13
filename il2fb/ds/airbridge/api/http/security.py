# coding: utf-8

import aiohttp_cors

from aiohttp import web


def setup_cors(app: web.Application) -> None:
    defaults = {
        key: aiohttp_cors.ResourceOptions(**value)
        for key, value in app['config']['cors'].items()
    }
    cors = aiohttp_cors.setup(app, defaults=defaults)

    for route in app.router.routes():
        cors.add(route)
