# coding: utf-8

from aiohttp import web

from .views import http_health


def setup_routes(app: web.Application) -> None:
    app.router.add_get(
        '/health', http_health,
    )
