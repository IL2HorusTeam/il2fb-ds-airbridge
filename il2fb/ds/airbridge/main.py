# coding: utf-8

import argparse
import asyncio
import functools
import logging
import sys
import time

from pathlib import Path

import psutil

from ddict import DotAccessDict

from il2fb.config.ds import ServerConfig
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from il2fb.ds.airbridge.application import Airbridge
from il2fb.ds.airbridge.compat import IS_WINDOWS
from il2fb.ds.airbridge.config import load_config
from il2fb.ds.airbridge.dedicated_server.instance import DedicatedServer
from il2fb.ds.airbridge.dedicated_server.validators import validate_dedicated_server_config
from il2fb.ds.airbridge.exceptions import AirbridgeException
from il2fb.ds.airbridge.logging import setup_logging
from il2fb.ds.airbridge.state import track_persistent_state
from il2fb.ds.airbridge.terminal import Terminal


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


def wait_for_dedicated_server_ports(
    pid: int,
    config: ServerConfig,
    timeout: float=3,
) -> None:

    process = psutil.Process(pid)
    expected_ports = {
        config.connection.port,
        config.console.connection.port,
        config.device_link.connection.port,
    }

    while timeout > 0:
        start_time = time.monotonic()

        actual_ports = {c.laddr.port for c in process.connections('inet')}
        if actual_ports == expected_ports:
            return

        delay = min(timeout, 0.1)
        time.sleep(delay)

        time_delta = time.monotonic() - start_time
        timeout = max(0, timeout - time_delta)

    raise RuntimeError("expected ports of dedicated server are closed")


def set_exit_handler(loop, handler) -> None:
    if IS_WINDOWS:
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(handler, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception(f"pypiwin32 is not installed for Python {version}")
    else:
        import signal
        loop.add_signal_handler(signal.SIGINT, handler)
        loop.add_signal_handler(signal.SIGTERM, handler)


def handle_exit(loop, ds, *args, **kwargs) -> None:
    LOG.info("got signal to exit")
    loop.create_task(ds.ask_exit())


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

    ds.ask_exit()
    return_code = ds.wait_finished()

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


def run(
    loop: asyncio.AbstractEventLoop,
    config: ServerConfig,
    state: DotAccessDict,
) -> None:
    LOG.info("init dedicated server")

    terminal = Terminal()

    ds_exit_future = asyncio.Future(loop=loop)
    ds_exit_function = functools.partial(ds_exit_future.set_result, None)

    try:
        ds = DedicatedServer(
            exe_path=config.ds.exe_path,
            config_path=config.ds.get('config_path'),
            start_script_path=config.ds.get('start_script_path'),
            wine_bin_path=config.wine_bin_path,
            stdout_handler=terminal.handle_stdout,
            stderr_handler=terminal.handle_stderr,
            prompt_handler=terminal.handle_prompt,
            exit_cb=ds_exit_function,
        )
    except Exception:
        LOG.fatal("failed to init dedicated server", exc_info=True)
        abort()

    LOG.info("validate config of dedicated server")

    try:
        validate_dedicated_server_config(ds.config)
    except ValueError as e:
        LOG.fatal(e)
        abort()

    LOG.info("wait for dedicated server to boot")

    try:
        ds.start()
    except Exception:
        LOG.fatal("failed to start dedicated server", exc_info=True)
        abort()

    LOG.info("wait for dedicated server to open ports")

    try:
        wait_for_dedicated_server_ports(ds.pid, ds.config)
    except Exception as e:
        LOG.fatal(e)
        ds.terminate()
        ds.wait_finished()
        abort()

    LOG.info("start input handler")

    terminal.listen_stdin(handler=ds.input)

    LOG.info("init dedicated server clients")

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

    LOG.info("set exit handler")

    exit_handler = functools.partial(handle_exit, loop, ds)
    set_exit_handler(loop, exit_handler)

    LOG.info("init application")

    app = Airbridge(
        loop=loop,
        config=config,
        state=state,
        dedicated_server=ds,
        console_client=console_client,
        device_link_client=dl_client,
    )

    LOG.info("start application")

    app_start_task = loop.create_task(app.start())
    loop.run_until_complete(app_start_task)

    try:
        LOG.info("run")
        loop.run_until_complete(ds_exit_future)
    except AirbridgeException:
        LOG.fatal("fatal error has occured")
    except Exception:
        LOG.fatal("fatal error has occured", exc_info=True)
    else:
        finish(loop, app, console_client, dl_client)

    terminate(loop, ds, app, console_client, dl_client)


def main():
    args = load_args()
    loop = asyncio.get_event_loop()
    config = load_config(args.config_path)

    setup_logging(config.logging)

    with track_persistent_state(config.state.file_path) as state:
        run(loop, config, state)


if __name__ == '__main__':
    main()
