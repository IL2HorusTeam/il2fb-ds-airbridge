# coding: utf-8

import argparse
import asyncio
import logging

from pathlib import Path
from typing import Awaitable

import psutil

from autologging import traced
from ddict import DotAccessDict

from il2fb.config.ds import ServerConfig
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from il2fb.ds.airbridge.application import Airbridge
from il2fb.ds.airbridge.config import load_config
from il2fb.ds.airbridge.dedicated_server.process import DedicatedServer
from il2fb.ds.airbridge.exceptions import AirbridgeException
from il2fb.ds.airbridge.logging import setup_logging
from il2fb.ds.airbridge.state import track_persistent_state
from il2fb.ds.airbridge.terminal import Terminal
from il2fb.ds.airbridge.typing import StringHandler


LOG = logging.getLogger(__name__)


def load_args():
    parser = argparse.ArgumentParser(
        description=(
            "Wrapper of dedicated server of "
            "«IL-2 Sturmovik: Forgotten Battles»"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-c', '--config',
        dest='config_path',
        type=lambda x: Path(x).resolve(),
        default='airbridge.yml',
        help="path to config file",
    )
    return parser.parse_args()


def make_thread_safe_string_handler(
    loop: asyncio.AbstractEventLoop,
    handler: StringHandler,
) -> StringHandler:

    def thread_safe_handler(s: str) -> None:
        asyncio.run_coroutine_threadsafe(handler(s), loop)

    return thread_safe_handler


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


@traced(LOG)
async def wait_for_dedicated_server_ports(
    loop: asyncio.AbstractEventLoop,
    pid: int,
    config: ServerConfig,
    timeout: float=3,
) -> Awaitable[None]:

    process = psutil.Process(pid)
    expected_ports = {
        config.connection.port,
        config.console.connection.port,
        config.device_link.connection.port,
    }

    while timeout > 0:
        start_time = loop.time()

        actual_ports = {c.laddr.port for c in process.connections('inet')}
        if actual_ports == expected_ports:
            return

        delay = min(timeout, 0.1)
        await asyncio.sleep(delay, loop=loop)

        time_delta = loop.time() - start_time
        timeout = max(0, timeout - time_delta)

    raise RuntimeError("expected ports of dedicated server are closed")


def abort(exit_code: int=-1):
    LOG.fatal("abort")
    raise SystemExit(exit_code)


def terminate(
    loop: asyncio.AbstractEventLoop,
    ds: DedicatedServer,
    app: Airbridge,
    console_client: ConsoleClient,
    dl_client: DeviceLinkClient,
):
    app.stop()
    console_client.close()
    dl_client.close()
    ds.stop()

    return_code = loop.run_until_complete(ds.wait_stopped())
    if return_code is None:
        return_code = -1

    loop.run_until_complete(asyncio.gather(
        app.wait_stopped(),
        console_client.wait_closed(),
        dl_client.wait_closed(),
        loop=loop,
    ))

    LOG.fatal("terminate")
    raise SystemExit(return_code)


def finish(
    loop: asyncio.AbstractEventLoop,
    app: Airbridge,
    console_client: ConsoleClient,
    dl_client: DeviceLinkClient,
):
    app.stop()
    console_client.close()
    dl_client.close()

    loop.run_until_complete(asyncio.gather(
        app.wait_stopped(),
        console_client.wait_closed(),
        dl_client.wait_closed(),
        loop=loop,
    ))

    LOG.info("exit")
    raise SystemExit(0)


def run(config: ServerConfig, state: DotAccessDict) -> None:
    LOG.info("init application")

    loop = asyncio.get_event_loop()
    terminal = Terminal()

    try:
        ds = DedicatedServer(
            loop=loop,
            exe_path=config.ds.exe_path,
            config_path=config.ds.get('config_path'),
            start_script_path=config.ds.get('start_script_path'),
            wine_bin_path=config.wine_bin_path,
            stdout_handler=terminal.handle_stdout,
            stderr_handler=terminal.handle_stderr,
            prompt_handler=terminal.handle_prompt,
        )
    except Exception:
        LOG.fatal("failed to init dedicated server", exc_info=True)
        abort()

    try:
        validate_dedicated_server_config(ds.config)
    except ValueError as e:
        LOG.fatal(e)
        abort()

    ds_start_task = loop.create_task(ds.start())

    LOG.info("wait for server to start")

    try:
        loop.run_until_complete(ds_start_task)
    except Exception:
        ds_start_task.cancel()
        LOG.fatal("failed to start dedicated server", exc_info=True)
        abort()

    try:
        future = wait_for_dedicated_server_ports(loop, ds.pid, ds.config)
        loop.run_until_complete(future)
    except Exception as e:
        LOG.fatal(e)
        ds.stop()
        loop.run_until_complete(ds.wait_stopped())
        abort()

    LOG.info("start input handler")

    stdin_handler = make_thread_safe_string_handler(loop, ds.input)
    terminal.listen_stdin(handler=stdin_handler)

    LOG.info("init clients")

    console_client = ConsoleClient(loop=loop)
    loop.create_task(loop.create_connection(
        protocol_factory=lambda: console_client,
        host=(ds.config.connection.host or "localhost"),
        port=ds.config.console.connection.port,
    ))

    dl_address = (
        (ds.config.device_link.connection.host or "localhost"),
        ds.config.device_link.connection.port,
    )
    dl_client = DeviceLinkClient(
        remote_address=dl_address,
        loop=loop,
    )
    loop.create_task(loop.create_datagram_endpoint(
        protocol_factory=lambda: dl_client,
        remote_addr=dl_address,
    ))

    loop.run_until_complete(asyncio.gather(
        console_client.wait_connected(),
        dl_client.wait_connected(),
        loop=loop,
    ))

    app = Airbridge(
        loop=loop,
        config=config,
        state=state,
        dedicated_server=ds,
        console_client=console_client,
        device_link_client=dl_client,
    )
    app_start_task = loop.create_task(app.start())
    loop.run_until_complete(app_start_task)

    try:
        LOG.info("run")
        loop.run_until_complete(ds.wait_stopped())
    except KeyboardInterrupt:
        LOG.warning("interrupted by user")
    except AirbridgeException:
        LOG.fatal("fatal error has occured")
    except Exception:
        LOG.fatal("fatal error has occured", exc_info=True)
    else:
        finish(loop, app, console_client, dl_client)

    terminate(loop, ds, app, console_client, dl_client)


def main():
    args = load_args()

    config = load_config(args.config_path)
    setup_logging(config.logging)

    with track_persistent_state(config.state.file_path) as state:
        run(config, state)


if __name__ == '__main__':
    main()
