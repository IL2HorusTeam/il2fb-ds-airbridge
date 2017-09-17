# coding: utf-8

import argparse
import asyncio
import io
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
from typing import Awaitable, Callable, Optional

from colorama import init as init_colors, Fore, Style
from funcy import log_calls

from il2fb.ds.airbridge.application import Airbridge
from il2fb.ds.airbridge.exceptions import AirbridgeException
from il2fb.ds.airbridge.config import load_config
from il2fb.ds.airbridge.logging import setup_logging


LOG = logging.getLogger(__name__)


StringProducer = Callable[[], str]
StringHandler = Callable[[str], None]


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


def get_loop() -> asyncio.AbstractEventLoop:
    if platform.system() == 'Windows':
        return asyncio.ProactorEventLoop()

    return asyncio.SelectorEventLoop()


def colorize_prompt(s: str) -> str:
    return f"{Fore.GREEN}{s}{Style.RESET_ALL}"


def colorize_error(s: str) -> str:
    return f"{Fore.RED}{s}{Style.RESET_ALL}"


def write_string_to_stream(stream: io.RawIOBase, s: str) -> None:
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

    def __init__(self, idle_handler: StringHandler):
        self._value = self._empty_value
        self._mutex = threading.Lock()
        self._not_empty = threading.Condition(self._mutex)
        self._is_waiting = True
        self._idle_handler = idle_handler

    @property
    def is_empty(self) -> bool:
        return self._value is self._empty_value

    def reset(self) -> None:
        self._value = self._empty_value

    @log_calls(LOG.debug, errors=False)
    def put(self, value: Optional[str]):
        with self._not_empty:
            if self._is_waiting:
                self._value = value
                self._not_empty.notify()
            else:
                self._idle_handler(value)

    @log_calls(LOG.debug, errors=False)
    def pop(self) -> Optional[str]:
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


@log_calls(LOG.debug, errors=False)
def read_input(
    prompt_getter: StringProducer,
    input_handler: StringHandler,
) -> None:

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


def make_thread_safe_input_handler(
    loop: asyncio.AbstractEventLoop,
    handler: StringHandler,
) -> StringHandler:

    def thread_safe_handler(s: str) -> None:
        asyncio.run_coroutine_threadsafe(handler(s), loop)

    return thread_safe_handler


def make_prompt_resetting_input_handler(
    prompt: Prompt,
    handler: StringHandler,
) -> StringHandler:

    def resetting_handler(s: str) -> None:
        with prompt:
            prompt.reset()
            handler(s)

    return resetting_handler


def run_or_exit(
    loop: asyncio.AbstractEventLoop,
    app: Airbridge,
    awaitable: Awaitable,
) -> None:

    try:
        loop.run_until_complete(awaitable)
    except KeyboardInterrupt:
        LOG.warning("interrupted by user")
    except AirbridgeException:
        LOG.fatal("fatal error has occured")
    except Exception:
        LOG.fatal("fatal error has occured", exc_info=True)
    else:
        return

    app.exit()

    return_code = loop.run_until_complete(app.wait_exit())
    if return_code is None:
        return_code = -1

    LOG.fatal("terminate application")
    raise SystemExit(return_code)


def main():
    args = load_args()
    config = load_config(args.config_path)
    setup_logging(config.logging)

    LOG.info("init application")

    readline.clear_history()
    init_colors()

    loop = get_loop()
    loop.set_debug(config.debug)
    asyncio.set_event_loop(loop)

    prompt = Prompt(idle_handler=print_prompt)

    app = Airbridge(
        loop=loop,
        config=config,

        stdout_handler=write_string_to_stdout,
        stderr_handler=lambda s: write_string_to_stderr(colorize_error(s)),
        passive_prompt_handler=print_prompt,
        active_prompt_handler=prompt.put,
    )
    app_task = loop.create_task(app.run())

    LOG.info("wait for application to boot")
    run_or_exit(loop, app, app.wait_boot())

    input_handler = make_thread_safe_input_handler(loop, app.user_input)
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

    LOG.info("run application")
    run_or_exit(loop, app, app_task)
    LOG.info("exit application")


if __name__ == '__main__':
    main()
