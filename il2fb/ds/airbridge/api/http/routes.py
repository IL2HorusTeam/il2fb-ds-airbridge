# coding: utf-8

from aiohttp import web

from il2fb.ds.airbridge.api.http import views


def setup_routes(app: web.Application) -> None:
    app.router.add_get(
        '/health', views.get_health,
    )
    app.router.add_get(
        '/info', views.get_server_info,
    )

    app.router.add_get(
        '/humans', views.get_humans_list,
    )
    app.router.add_get(
        '/humans/count', views.get_humans_count,
    )
    app.router.add_get(
        '/humans/statistics', views.get_humans_statistics,
    )
    app.router.add_post(
        '/humans/kick', views.kick_all_humans,
    )
    app.router.add_post(
        '/humans/{callsign}/kick', views.kick_human_by_callsign,
    )

    app.router.add_post(
        '/chat', views.chat_to_all,
    )
    app.router.add_post(
        '/chat/humans/{callsign}', views.chat_to_human,
    )
    app.router.add_post(
        '/chat/belligerents/{belligerent}', views.chat_to_belligerent,
    )

    app.router.add_get(
        '/missions/current/info', views.get_current_mission_info,
    )
    app.router.add_post(
        '/missions/current/begin', views.begin_current_mission,
    )
    app.router.add_post(
        '/missions/current/end', views.end_current_mission,
    )
    app.router.add_post(
        '/missions/current/unload', views.unload_current_mission,
    )
    app.router.add_post(
        '/missions/load', views.load_mission,
    )
    app.router.add_delete(
        '/missions/{file_path:[^{}]+\.mis}', views.delete_mission,
    )
    app.router.add_get(
        '/missions', views.browse_missions,
    )
    app.router.add_post(
        '/missions', views.upload_mission,
    )

    app.router.add_get(
        '/radar/ships', views.get_all_ships_positions,
    )
    app.router.add_get(
        '/radar/ships/moving', views.get_moving_ships_positions,
    )
    app.router.add_get(
        '/radar/ships/stationary', views.get_stationary_ships_positions,
    )
    app.router.add_get(
        '/radar/aircrafts/moving', views.get_moving_aircrafts_positions,
    )
    app.router.add_get(
        '/radar/ground-units/moving', views.get_moving_ground_units_positions,
    )
    app.router.add_get(
        '/radar/houses', views.get_all_houses_positions,
    )
    app.router.add_get(
        '/radar/stationary-objects', views.get_stationary_objects_positions,
    )
    app.router.add_get(
        '/radar/moving', views.get_all_moving_actors_positions,
    )
    app.router.add_get(
        '/radar/stationary', views.get_all_stationary_actors_positions,
    )
