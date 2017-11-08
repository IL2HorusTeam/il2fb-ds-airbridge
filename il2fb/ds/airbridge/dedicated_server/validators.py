# coding: utf-8

import os

from il2fb.config.ds import ServerConfig


def validate_dedicated_server_file_access(file_path):
    if not os.access(file_path, os.F_OK):
        raise FileNotFoundError(
            f"file does not exist (path='{file_path}')"
        )

    if not os.access(file_path, os.R_OK):
        raise PermissionError(
            f"file does not have read access (path='{file_path}')"
        )


def validate_dedicated_server_config(config: ServerConfig) -> None:
    if not config.console.connection.port:
        raise ValueError(
            "server's console is disabled, please enable it "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#console-section)"
        )

    if not config.device_link.connection.port:
        raise ValueError(
            "server's device link is disabled, please enable it "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#devicelink-section)"
        )
