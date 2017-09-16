# coding: utf-8

import argparse
import asyncio
import logging
import math
import platform
import sys
import threading

try:
    import readline
except ImportError:
    import pyreadline as readline

from pathlib import Path

import psutil

from colorama import init as init_colors, Fore, Style

from il2fb.ds.airbridge.config import load_config
from il2fb.ds.airbridge.dedicated_server import DedicatedServer
from il2fb.ds.airbridge.logging import setup_logging


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


def write_string_to_stdout(s: str) -> None:
    write_string_to_stream(sys.stdout, s)


def write_string_to_stderr(s: str) -> None:
    write_string_to_stream(sys.stderr, s)


def print_prompt(s: str) -> None:
    write_string_to_stdout(colorize_prompt(s))


class Prompt:
    _empty_value = math.nan

    def __init__(self, idle_handler):
        self._value = self._empty_value
        self._mutex = threading.Lock()
        self._not_empty = threading.Condition(self._mutex)
        self._is_waiting = True
        self._idle_handler = idle_handler

    @property
    def is_empty(self) -> bool:
        return self._value is self._empty_value

    def reset(self):
        self._value = self._empty_value

    def put(self, value):
        with self._not_empty:
            if self._is_waiting:
                self._value = value
                self._not_empty.notify()
            else:
                self._idle_handler(value)

    def pop(self):
        with self._not_empty:
            self._is_waiting = True

            while self.is_empty:
                self._not_empty.wait()

            value, self._value = self._value, self._empty_value
            self._is_waiting = False

        return value

    def __enter__(self):
        self._mutex.acquire()

    def __exit__(self, type, value, traceback):
        self._mutex.release()


def read_input(prompt_getter, input_handler):
    while True:
        prompt = prompt_getter()

        if prompt is None:
            return

        user_input = input(prompt)
        line = user_input + '\n'

        try:
            input_handler(line)
        except Exception:
            LOG.exception(f"failed to handle input line '{line}'")

        if line == 'exit':
            return


def make_thread_safe_input_handler(loop, handler):

    def thread_safe_handler(s: str) -> None:
        asyncio.run_coroutine_threadsafe(handler(s), loop)

    return thread_safe_handler


def make_prompt_resetting_input_handler(prompt, handler):

    def resetting_handler(s: str) -> None:
        with prompt:
            prompt.reset()
            handler(s)

    return resetting_handler


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
    loop, pid, config, timeout=5,
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
    prompt = Prompt(idle_handler=print_prompt)

    try:
        ds = DedicatedServer(
            loop=loop,
            exe_path=config.ds.exe_path,
            config_path=config.ds.get('config_path'),
            start_script_path=config.ds.get('start_script_path'),
            wine_bin_path=config.wine_bin_path,
            stdout_handler=write_string_to_stdout,
            stderr_handler=lambda s: write_string_to_stderr(colorize_error(s)),
            passive_prompt_handler=print_prompt,
            active_prompt_handler=prompt.put,
        )
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
    input_handler = make_prompt_resetting_input_handler(prompt, input_handler)
    input_thread = threading.Thread(
        target=read_input,
        kwargs=dict(
            prompt_getter=lambda: colorize_prompt(prompt.pop()),
            input_handler=input_handler,
        ),
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


if __name__ == '__main__':
    main()
