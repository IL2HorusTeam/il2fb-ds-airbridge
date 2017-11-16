# coding: utf-8

from aiohttp.abc import AbstractRouter

from il2fb.ds.airbridge.api.http.views import chat
from il2fb.ds.airbridge.api.http.views import humans
from il2fb.ds.airbridge.api.http.views import misc
from il2fb.ds.airbridge.api.http.views import missions
from il2fb.ds.airbridge.api.http.views import radar
from il2fb.ds.airbridge.api.http.views.streaming import StreamingView


def setup_routes(router: AbstractRouter) -> None:
    router.add_get('/health', misc.get_health)
    router.add_get('/info', misc.get_server_info)
    router.add_get('/streaming', StreamingView)

    _setup_humans_routes(router)
    _setup_chat_routes(router)
    _setup_missions_routes(router)
    _setup_radar_routes(router)


def _setup_humans_routes(router: AbstractRouter) -> None:
    router.add_post(
        '/humans/{callsign}/kick', humans.kick_human_by_callsign,
    )
    router.add_post(
        '/humans/kick', humans.kick_all_humans,
    )
    router.add_get(
        '/humans/statistics', humans.get_humans_statistics,
    )
    router.add_get(
        '/humans/count', humans.get_humans_count,
    )
    router.add_get(
        '/humans', humans.get_humans_list,
    )


def _setup_chat_routes(router: AbstractRouter) -> None:
    router.add_post(
        '/chat/humans/{callsign}', chat.chat_to_human,
    )
    router.add_post(
        '/chat/belligerents/{belligerent}', chat.chat_to_belligerent,
    )
    router.add_post(
        '/chat', chat.chat_to_all,
    )


def _setup_missions_routes(router: AbstractRouter) -> None:
    router.add_get(
        '/missions/current/info', missions.get_current_mission_info,
    )
    router.add_post(
        '/missions/current/begin', missions.begin_current_mission,
    )
    router.add_post(
        '/missions/current/end', missions.end_current_mission,
    )
    router.add_post(
        '/missions/current/unload', missions.unload_current_mission,
    )
    router.add_post(
        '/missions/{file_path:[^{}]+\.mis}/load', missions.load_mission,
    )
    router.add_delete(
        '/missions/{file_path:[^{}]+\.mis}', missions.delete_mission,
    )
    router.add_get(
        '/missions/{file_path:[^{}]+\.mis}', missions.get_mission,
    )
    router.add_post(
        '/missions/{dir_path:[^{}]*}', missions.upload_mission,
    )
    router.add_get(
        '/missions/{dir_path:[^{}]*}', missions.browse_missions,
    )
    router.add_post(
        '/missions', missions.upload_mission,
    )
    router.add_get(
        '/missions', missions.browse_missions,
    )


def _setup_radar_routes(router: AbstractRouter) -> None:
    router.add_get(
        '/radar/ships', radar.get_all_ships_positions,
    )
    router.add_get(
        '/radar/ships/moving', radar.get_moving_ships_positions,
    )
    router.add_get(
        '/radar/ships/stationary', radar.get_stationary_ships_positions,
    )
    router.add_get(
        '/radar/aircrafts/moving', radar.get_moving_aircrafts_positions,
    )
    router.add_get(
        '/radar/ground-units/moving', radar.get_moving_ground_units_positions,
    )
    router.add_get(
        '/radar/houses', radar.get_all_houses_positions,
    )
    router.add_get(
        '/radar/stationary-objects', radar.get_stationary_objects_positions,
    )
    router.add_get(
        '/radar/moving', radar.get_all_moving_actors_positions,
    )
    router.add_get(
        '/radar/stationary', radar.get_all_stationary_actors_positions,
    )
