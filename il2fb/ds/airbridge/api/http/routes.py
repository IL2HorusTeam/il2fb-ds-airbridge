# coding: utf-8

from aiohttp import web

from il2fb.ds.airbridge.api.http.views import get_health
from il2fb.ds.airbridge.api.http.views import get_server_info

from il2fb.ds.airbridge.api.http.views import get_humans_count
from il2fb.ds.airbridge.api.http.views import get_humans_list
from il2fb.ds.airbridge.api.http.views import get_humans_statistics

from il2fb.ds.airbridge.api.http.views import kick_all_humans
from il2fb.ds.airbridge.api.http.views import kick_human_by_callsign

from il2fb.ds.airbridge.api.http.views import chat_to_all
from il2fb.ds.airbridge.api.http.views import chat_to_belligerent
from il2fb.ds.airbridge.api.http.views import chat_to_human

from il2fb.ds.airbridge.api.http.views import browse_missions
from il2fb.ds.airbridge.api.http.views import upload_mission
from il2fb.ds.airbridge.api.http.views import load_mission
from il2fb.ds.airbridge.api.http.views import get_current_mission_info
from il2fb.ds.airbridge.api.http.views import begin_current_mission
from il2fb.ds.airbridge.api.http.views import end_current_mission
from il2fb.ds.airbridge.api.http.views import unload_current_mission

from il2fb.ds.airbridge.api.http.views import get_all_ships_positions
from il2fb.ds.airbridge.api.http.views import get_moving_ships_positions
from il2fb.ds.airbridge.api.http.views import get_stationary_ships_positions
from il2fb.ds.airbridge.api.http.views import get_moving_aircrafts_positions
from il2fb.ds.airbridge.api.http.views import get_moving_ground_units_positions
from il2fb.ds.airbridge.api.http.views import get_all_houses_positions
from il2fb.ds.airbridge.api.http.views import get_stationary_objects_positions
from il2fb.ds.airbridge.api.http.views import get_all_moving_actors_positions
from il2fb.ds.airbridge.api.http.views import get_all_stationary_actors_positions


def setup_routes(app: web.Application) -> None:
    app.router.add_get(
        '/health', get_health,
    )
    app.router.add_get(
        '/info', get_server_info,
    )
    app.router.add_get(
        '/humans', get_humans_list,
    )
    app.router.add_get(
        '/humans/count', get_humans_count,
    )
    app.router.add_get(
        '/humans/statistics', get_humans_statistics,
    )
    app.router.add_post(
        '/humans/kick', kick_all_humans,
    )
    app.router.add_post(
        '/humans/{callsign}/kick', kick_human_by_callsign,
    )
    app.router.add_post(
        '/chat', chat_to_all,
    )
    app.router.add_post(
        '/chat/humans/{callsign}', chat_to_human,
    )
    app.router.add_post(
        '/chat/belligerents/{belligerent}', chat_to_belligerent,
    )
    app.router.add_get(
        '/missions', browse_missions,
    )
    app.router.add_post(
        '/missions', upload_mission,
    )
    app.router.add_post(
        '/missions/load', load_mission,
    )
    app.router.add_get(
        '/missions/current/info', get_current_mission_info,
    )
    app.router.add_post(
        '/missions/current/begin', begin_current_mission,
    )
    app.router.add_post(
        '/missions/current/end', end_current_mission,
    )
    app.router.add_post(
        '/missions/current/unload', unload_current_mission,
    )
    app.router.add_get(
        '/radar/ships', get_all_ships_positions,
    )
    app.router.add_get(
        '/radar/ships/moving', get_moving_ships_positions,
    )
    app.router.add_get(
        '/radar/ships/stationary', get_stationary_ships_positions,
    )
    app.router.add_get(
        '/radar/aircrafts/moving', get_moving_aircrafts_positions,
    )
    app.router.add_get(
        '/radar/ground-units/moving', get_moving_ground_units_positions,
    )
    app.router.add_get(
        '/radar/houses', get_all_houses_positions,
    )
    app.router.add_get(
        '/radar/stationary-objects', get_stationary_objects_positions,
    )
    app.router.add_get(
        '/radar/moving', get_all_moving_actors_positions,
    )
    app.router.add_get(
        '/radar/stationary', get_all_stationary_actors_positions,
    )
