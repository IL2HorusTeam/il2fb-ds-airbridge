# coding: utf-8

from il2fb.config.ds import ServerConfig


def validate_dedicated_server_config(config: ServerConfig) -> None:
    if not config.console.connection.port:
        raise ValueError(
            "server's console is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#console-section)"
        )

    if not config.device_link.connection.port:
        raise ValueError(
            "server's device link is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#devicelink-section)"
        )
