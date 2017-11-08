# coding: utf-8

import argparse
import asyncio
import functools
import logging
import sys
import threading

from pathlib import Path
from typing import Awaitable, Callable

from ddict import DotAccessDict

from il2fb.config.ds import ServerConfig
from il2fb.ds.middleware.console.client import ConsoleClient
from il2fb.ds.middleware.device_link.client import DeviceLinkClient

from il2fb.ds.airbridge.application import Airbridge
from il2fb.ds.airbridge.compat import IS_WINDOWS
from il2fb.ds.airbridge.config import load_config
from il2fb.ds.airbridge.dedicated_server.instance import DedicatedServer
from il2fb.ds.airbridge.exceptions import AirbridgeException
from il2fb.ds.airbridge.logging import setup_logging
from il2fb.ds.airbridge.state import track_persistent_state
from il2fb.ds.airbridge.terminal import Terminal
from il2fb.ds.airbridge.typing import StringHandler, BoolOrNone


LOG = logging.getLogger(__name__)


def load_args() -> argparse.Namespace:
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


def wrap_exit_handler(thread, exit_handler) -> BoolOrNone:

    def wrapped_exit_handler(*args, **kwargs):
        if IS_WINDOWS:
            threading.current_thread().name = "exit worker"

        LOG.info("got signal to exit")
        exit_handler()

        if IS_WINDOWS:
            thread.join()
            return True

    return wrapped_exit_handler


def set_exit_handler(loop: asyncio.AbstractEventLoop, handler) -> None:
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


def abort(exit_code: int=-1):
    LOG.fatal("abort")
    raise SystemExit(exit_code)


def run_app(
    loop: asyncio.AbstractEventLoop,
    dedicated_server: DedicatedServer,
    config: ServerConfig,
    state: DotAccessDict,
    start_ack: Callable[[], None],
    error_ack: Callable[[], None],
    stop_request: Awaitable[None],
) -> None:
    asyncio.set_event_loop(loop)

    LOG.info("init dedicated server clients")

    console_client = ConsoleClient(loop=loop)
    loop.create_task(loop.create_connection(
        protocol_factory=lambda: console_client,
        host=dedicated_server.config.connection.host or "localhost",
        port=dedicated_server.config.console.connection.port,
    ))

    device_link_address = (
        dedicated_server.config.device_link.connection.host or "localhost",
        dedicated_server.config.device_link.connection.port,
    )
    device_link_client = DeviceLinkClient(
        loop=loop,
        remote_address=device_link_address,
    )

    loop.create_task(loop.create_datagram_endpoint(
        protocol_factory=lambda: device_link_client,
        remote_addr=device_link_client.remote_address,
    ))

    loop.run_until_complete(asyncio.gather(
        console_client.wait_connected(),
        device_link_client.wait_connected(),
        loop=loop,
    ))

    LOG.info("create application")

    app = Airbridge(
        loop=loop,
        config=config,
        state=state,
        dedicated_server=dedicated_server,
        console_client=console_client,
        device_link_client=device_link_client,
    )

    LOG.info("start application")

    app_start_task = loop.create_task(app.start())
    loop.run_until_complete(app_start_task)
    start_ack()

    try:
        LOG.info("run application until stop is requested")
        loop.run_until_complete(stop_request)
    except AirbridgeException:
        LOG.fatal("fatal error has occured")
    except Exception:
        LOG.fatal("fatal error has occured", exc_info=True)
        error_ack()
    else:
        LOG.info("application stop was requested")
        error_ack()
    finally:
        app.stop()
        console_client.close()
        device_link_client.close()

        loop.run_until_complete(asyncio.gather(
            app.wait_stopped(),
            console_client.wait_closed(),
            device_link_client.wait_closed(),
            loop=loop,
        ))


def run_main(config: ServerConfig, state: DotAccessDict) -> None:
    main_thread = threading.current_thread()
    main_thread.name = "main"

    LOG.info("init dedicated server")

    main_loop = (
        asyncio.ProactorEventLoop()
        if IS_WINDOWS
        else asyncio.SelectorEventLoop()
    )
    asyncio.set_event_loop(main_loop)

    terminal = Terminal()

    try:
        ds = DedicatedServer(
            loop=main_loop,
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

    LOG.info("start dedicated server")

    ds_start_task = main_loop.create_task(ds.start())

    try:
        main_loop.run_until_complete(ds_start_task)
    except Exception:
        ds_start_task.cancel()
        LOG.fatal("failed to start dedicated server", exc_info=True)
        abort()

    LOG.info("wait for dedicated server to boot")

    try:
        main_loop.run_until_complete(ds.wait_network_listeners())
    except Exception as e:
        LOG.fatal(e)
        ds.terminate()
        main_loop.run_until_complete(ds.wait_finished())
        abort()

    LOG.info("start input handler")

    stdin_handler = make_thread_safe_string_handler(main_loop, ds.input)
    terminal.listen_stdin(handler=stdin_handler)

    LOG.info("prepare for application start")

    app_loop = asyncio.SelectorEventLoop()

    app_start_event = asyncio.Event(loop=main_loop)
    app_start_event.clear()

    app_stop_event = asyncio.Event(loop=app_loop)
    app_stop_event.clear()

    app_start_ack = functools.partial(
        main_loop.call_soon_threadsafe,
        app_start_event.set,
    )
    app_error_ack = functools.partial(
        main_loop.call_soon_threadsafe,
        ds.ask_exit,
    )
    app_stop_request = app_stop_event.wait()

    app_thread = threading.Thread(
        target=run_app,
        name="application",
        kwargs=dict(
            loop=app_loop,
            dedicated_server=ds,
            config=config,
            state=state,
            start_ack=app_start_ack,
            error_ack=app_error_ack,
            stop_request=app_stop_request,
        ),
        daemon=True,
    )

    app_thread.start()
    app_start_event.wait()

    LOG.info("set exit handler")

    exit_handler = functools.partial(main_loop.create_task, ds.ask_exit())
    exit_handler = wrap_exit_handler(main_thread, exit_handler)
    set_exit_handler(main_loop, exit_handler)

    try:
        LOG.info("wait for dedicated server to exit")
        return_code = main_loop.run_until_complete(ds.wait_finished())
    except KeyboardInterrupt:
        pass
    except Exception:
        LOG.fatal("failed to wait for dedicated server to exit", exc_info=True)
        return_code = -1
    else:
        LOG.info(f"dedicated server has exited (return_code={return_code})")
    finally:
        app_loop.call_soon_threadsafe(app_stop_event.set)
        app_thread.join()

        LOG.info("exit")
        raise SystemExit(return_code)


def main() -> None:
    args = load_args()

    config = load_config(args.config_path)
    setup_logging(config.logging)

    with track_persistent_state(config.state.file_path) as state:
        run_main(config, state)


if __name__ == '__main__':
    main()
