# coding: utf-8

import io
import logging
import math
import sys
import threading

try:
    import readline
except ImportError:
    import pyreadline as readline

from colorama import init as init_colors, Fore, Style

from il2fb.ds.airbridge.typing import StringHandler, StringOrNone


LOG = logging.getLogger(__name__)

EXIT_COMMAND = 'exit'


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


class Terminal:
    _prompt_empty_value = math.nan

    def __init__(self):
        readline.clear_history()
        init_colors()

        self._prompt_value = self._prompt_empty_value
        self._prompt_mutex = threading.Lock()
        self._prompt_not_empty = threading.Condition(self._prompt_mutex)
        self._prompt_has_waiters = True

        self._stdin_listener_thread = None
        self._stdin_listener_event = threading.Event()
        self._stdin_listener_event.clear()

    @staticmethod
    def handle_stdout(s: str) -> None:
        write_string_to_stdout(s)

    @staticmethod
    def handle_stderr(s: str) -> None:
        write_string_to_stderr(colorize_error(s))

    def handle_prompt(self, value: StringOrNone) -> None:
        with self._prompt_not_empty:
            if self._prompt_has_waiters:
                self._prompt_value = value
                self._prompt_not_empty.notify()

            if (
                (
                    value is not None
                ) and (
                    (not self._prompt_has_waiters)
                    or
                    self._stdin_listener_thread is None
                )
            ):
                write_string_to_stdout(colorize_prompt(value))

    def _pop_prompt(self) -> StringOrNone:
        with self._prompt_not_empty:
            self._prompt_has_waiters = True

            while self._prompt_is_empty:
                self._prompt_not_empty.wait()

            value, self._prompt_value = self._prompt_value, self._prompt_empty_value
            self._prompt_has_waiters = False

        return value

    @property
    def _prompt_is_empty(self) -> bool:
        return self._prompt_value is self._prompt_empty_value

    def _reset_prompt(self) -> None:
        self._prompt_value = self._prompt_empty_value
        self._prompt_has_waiters = True

    def listen_stdin(self, handler: StringHandler) -> None:
        with self._prompt_mutex:
            self._stdin_listener_thread = threading.Thread(
                target=self._listen_stdin,
                name="stdin",
                kwargs=dict(
                    handler=handler,
                ),
                daemon=True,
            )
            self._stdin_listener_thread.start()
            self._stdin_listener_event.wait()

    def _listen_stdin(self, handler: StringHandler) -> None:
        write_string_to_stdout("\r")
        self._stdin_listener_event.set()

        while True:
            prompt = self._pop_prompt()

            if prompt is None:
                return

            raw_line = input(colorize_prompt(prompt))
            line = raw_line + '\n'

            try:
                with self._prompt_mutex:
                    self._reset_prompt()
                    handler(line)
            except Exception:
                LOG.exception(f"failed to handle input line '{line}'")

            if raw_line == EXIT_COMMAND:
                return
