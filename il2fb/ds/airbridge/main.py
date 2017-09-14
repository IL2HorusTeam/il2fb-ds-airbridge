# coding: utf-8

import argparse
import asyncio
import functools
import logging
import platform
import queue
import readline
import sys

from pathlib import Path
from threading import Thread

import psutil

from colorama import init as init_colors, Fore, Style

from .config import load_config
from .dedicated_server import DedicatedServer
from .logging import setup_logging


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


def get_loop():
    if platform.system() == 'Windows':
        return asyncio.ProactorEventLoop()

    return asyncio.SelectorEventLoop()


def colorize_prompt(s: str) -> str:
    return f"{Fore.GREEN}{s}{Style.RESET_ALL}"


def colorize_error(s: str) -> str:
    return f"{Fore.RED}{s}{Style.RESET_ALL}"


def write_string_to_stream(stream, s: str) -> None:
    stream.write(s)
    stream.flush()


def read_input(prompt_getter, input_handler):
    while True:
        prompt = prompt_getter()

        if prompt is None:
            return

        user_input = input(colorize_prompt(prompt))
        line = user_input + '\n'

        try:
            input_handler(line)
        except Exception:
            LOG.exception(f"failed to handle input line '{line}'")

        if line == 'exit':
            return


def make_thread_safe_input_handler(loop, input_handler):

    def thread_safe_handler(s: str) -> None:
        asyncio.run_coroutine_threadsafe(input_handler(s), loop)

    return thread_safe_handler


def make_dedicated_server(loop, config, prompt_handler) -> DedicatedServer:
    config_path = config.ds.get('config_path')
    start_script_path = config.ds.get('start_script_path')

    stdout_writer = functools.partial(write_string_to_stream, sys.stdout)
    stderr_writer = functools.partial(write_string_to_stream, sys.stderr)

    return DedicatedServer(
        loop=loop,
        exe_path=config.ds.exe_path,
        config_path=config_path,
        start_script_path=start_script_path,
        wine_bin_path=config.wine_bin_path,
        stdout_handler=stdout_writer,
        stderr_handler=lambda s: stderr_writer(colorize_error(s)),
        passive_prompt_handler=lambda s: stdout_writer(colorize_prompt(s)),
        active_prompt_handler=prompt_handler,
    )


def validate_dedicated_server_config(config) -> None:
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


async def wait_for_dedicated_server_ports(
    loop, pid, config, timeout=30,
) -> None:
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

        delay = min(timeout, 1)
        asyncio.sleep(delay, loop=loop)
        time_delta = start_time - loop.time()
        timeout = max(0, timeout - time_delta)

    raise RuntimeError("expected ports of dedicated server are closed")


def main():
    readline.clear_history()
    init_colors()

    args = load_args()
    config = load_config(args.config_path)

    setup_logging(config.logging)

    loop = get_loop()
    asyncio.set_event_loop(loop)
    prompt_queue = queue.Queue()

    try:
        ds = make_dedicated_server(loop, config, prompt_queue.put_nowait)
    except Exception:
        LOG.fatal("failed to init dedicated server", exc_info=True)
        raise SystemExit(-1)

    try:
        validate_dedicated_server_config(ds.config)
    except ValueError as e:
        LOG.fatal(e)
        raise SystemExit(-1)

    ds_task = loop.create_task(ds.run())

    try:
        loop.run_until_complete(ds.wait_for_start())
    except Exception:
        ds_task.cancel()
        LOG.fatal("failed to start dedicated server", exc_info=True)
        raise SystemExit(-1)

    try:
        future = wait_for_dedicated_server_ports(loop, ds.pid, ds.config)
        loop.run_until_complete(future)
    except Exception as e:
        ds_task.cancel()
        LOG.fatal(e)
        raise SystemExit(-1)

    input_handler = make_thread_safe_input_handler(loop, ds.input)
    input_thread = Thread(
        target=read_input,
        args=(prompt_queue.get, input_handler),
        daemon=True,
    )
    input_thread.start()

    try:
        loop.run_until_complete(asyncio.gather(ds_task))
    except KeyboardInterrupt:
        LOG.info("interrupted by user")
    except Exception:
        LOG.fatal("fatal error has occured", exc_info=True)
        raise SystemExit(-1)
