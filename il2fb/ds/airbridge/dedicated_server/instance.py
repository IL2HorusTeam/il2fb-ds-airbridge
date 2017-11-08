# coding: utf-8

import asyncio
import configparser
import functools
import logging

from pathlib import Path
from typing import List, Awaitable

import psutil

from il2fb.config.ds import ServerConfig

from il2fb.ds.airbridge.compat import IS_WINDOWS
from il2fb.ds.airbridge.typing import IntOrNone, StringHandler, StringList
from il2fb.ds.airbridge.dedicated_server.path import (
    normalize_exe_path, normalize_config_path, normalize_start_script_path,
)
from il2fb.ds.airbridge.dedicated_server.validators import (
    validate_dedicated_server_file_access, validate_dedicated_server_config,
)


LOG = logging.getLogger(__name__)


def _try_to_load_config(path: str) -> ServerConfig:
    ini = configparser.ConfigParser()
    ini.read(path)
    return ServerConfig.from_ini(ini)


def _try_to_handle_string(handler, s: str) -> None:
    try:
        handler(s)
    except Exception:
        LOG.exception(f"failed to handle dedicated server's string '{s}'")


def _is_eol(char: str) -> bool:
    return char == '\n'


def _is_prompt(char: str, chars: StringList) -> bool:
    if char != '>':
        return False

    try:
        int(''.join(chars))
    except ValueError:
        return False
    else:
        return True


async def _read_stream_until_line(
    stream, stream_name, input_line, stop_line, output_handler=None,
    prompt_handler=None,
) -> Awaitable:

    chars = []

    stop_line_found = False

    while True:
        char = await stream.read(1)

        if not char:
            raise EOFError(
                f"dedicated server's {stream_name} stream was closed "
                f"unexpectedly"
            )

        char = char.decode()
        is_eol = _is_eol(char)
        is_prompt = (not is_eol) and _is_prompt(char, chars)
        chars.append(char)

        if not (is_eol or is_prompt):
            continue

        s, chars = ''.join(chars), []

        if s == stop_line:
            stop_line_found = True

        handler = (
            output_handler
            if is_eol
            else prompt_handler or output_handler
        )

        if handler:
            if stop_line_found and not is_prompt:
                handler(input_line)

            handler(s)

        if stop_line_found and is_prompt:
            break


async def _read_stream_until_end(
    stream, stream_name, output_handler, prompt_handler=None,
) -> Awaitable:

    chars = []

    while True:
        char = await stream.read(1)

        if not char:
            LOG.debug(f"dedicated server's {stream_name} stream was closed")
            break

        char = char.decode()
        is_eol = _is_eol(char)
        is_prompt = (not is_eol) and _is_prompt(char, chars)
        chars.append(char)

        if not (is_eol or is_prompt):
            continue

        s, chars = ''.join(chars), []
        handler = (
            output_handler
            if is_eol
            else prompt_handler or output_handler
        )

        handler(s)

    if chars:
        s, chars = ''.join(chars), []
        output_handler(s)


class DedicatedServer:

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        exe_path: str,
        start_script_path: str=None,
        config_path: str=None,
        wine_bin_path: str="wine",
        stdout_handler: StringHandler=None,
        stderr_handler: StringHandler=None,
        prompt_handler: StringHandler=None,
    ):
        self._loop = loop

        self.exe_path = normalize_exe_path(exe_path)
        validate_dedicated_server_file_access(self.exe_path)

        self.root_dir = self.exe_path.parent

        self.start_script_path = normalize_start_script_path(
            root_dir=self.root_dir,
            initial=start_script_path,
        )
        validate_dedicated_server_file_access(self.start_script_path)

        self.config_path = normalize_config_path(
            root_dir=self.root_dir,
            initial=config_path,
        )
        validate_dedicated_server_file_access(self.start_script_path)

        self.config = _try_to_load_config(self.config_path)
        validate_dedicated_server_config(self.config)

        self._wine_bin_path = wine_bin_path

        self.game_log_path = Path(self.config.events.logging.file_name)
        if not self.game_log_path.is_absolute():
            self.game_log_path = self.root_dir / self.game_log_path

        self._stdout_handler = (
            functools.partial(_try_to_handle_string, stdout_handler)
            if stdout_handler
            else None
        )
        self._stderr_handler = (
            functools.partial(_try_to_handle_string, stderr_handler)
            if stderr_handler
            else None
        )
        self._prompt_handler = (
            functools.partial(_try_to_handle_string, prompt_handler)
            if prompt_handler
            else None
        )

        self._process = None
        self._process_utils = None

        self._stream_handling_tasks = []

    @property
    def pid(self) -> IntOrNone:
        return self._process and self._process.pid

    async def start(self) -> Awaitable[None]:
        try:
            await self._spawn_process()
            self._maybe_setup_stderr_handler()
            await self._wait_started()
            self._maybe_setup_stdout_handler()
        except Exception:
            if self._process:
                self._process.kill()
                await self._process.wait()

            raise

    async def _spawn_process(self) -> Awaitable[None]:
        args = (
            []
            if IS_WINDOWS
            else [self._wine_bin_path]
        )
        args.extend([
            str(self.exe_path),
            '-conf', str(self.config_path),
            '-cmd', str(self.start_script_path),
        ])

        kwargs = dict(
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if not IS_WINDOWS:
            kwargs['start_new_session'] = True

        self._process = await asyncio.create_subprocess_exec(*args, **kwargs)
        self._process_utils = psutil.Process(self._process.pid)

    def _maybe_setup_stderr_handler(self) -> None:
        if not self._stderr_handler:
            return

        stream_task = self._loop.create_task(_read_stream_until_end(
            stream=self._process.stderr,
            stream_name="STDERR",
            output_handler=self._stderr_handler,
        ))
        self._stream_handling_tasks.append(stream_task)

    def _maybe_setup_stdout_handler(self) -> None:
        if not self._stdout_handler:
            return

        stream_task = self._loop.create_task(_read_stream_until_end(
            stream=self._process.stdout,
            stream_name="STDOUT",
            output_handler=self._stdout_handler,
            prompt_handler=self._prompt_handler,
        ))
        self._stream_handling_tasks.append(stream_task)

    async def _wait_started(self) -> Awaitable[List[asyncio.Task]]:
        input_line = "host\n"
        stop_line = "localhost: Server\n"

        boot_task = self._loop.create_task(_read_stream_until_line(
            stream=self._process.stdout,
            stream_name="STDOUT",
            input_line=input_line,
            stop_line=stop_line,
            output_handler=self._stdout_handler,
            prompt_handler=self._prompt_handler,
        ))

        await self.input(input_line)
        await boot_task

    async def wait_network_listeners(
        self,
        timeout: float=3,
        polling_period: float=0.1,
    ) -> Awaitable[None]:

        expected_ports = {
            self.config.connection.port,
            self.config.console.connection.port,
            self.config.device_link.connection.port,
        }

        while timeout > 0:
            start_time = self._loop.time()

            actual_ports = {
                c.laddr.port
                for c in self._process_utils.connections('inet')
            }

            if actual_ports == expected_ports:
                return

            delay = min(timeout, polling_period)
            await asyncio.sleep(delay, loop=self._loop)

            time_delta = self._loop.time() - start_time
            timeout = max(0, timeout - time_delta)

        raise RuntimeError("expected ports of dedicated server are closed")

    async def ask_exit(self) -> Awaitable[None]:
        await self.input("exit\n")

    def terminate(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()

    async def wait_finished(self) -> Awaitable[IntOrNone]:
        if self._stream_handling_tasks:
            await asyncio.gather(*self._stream_handling_tasks)

        if self._process:
            return_code = await self._process.wait()
            return return_code

    async def input(self, s: str) -> Awaitable[None]:
        if self._process:
            try:
                self._process.stdin.write(s.encode())
                await self._process.stdin.drain()
            except Exception:
                LOG.exception(f"failed to write string to STDIN (s={s})")
