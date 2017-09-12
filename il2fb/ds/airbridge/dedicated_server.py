# coding: utf-8

import asyncio
import configparser
import functools
import logging
import os
import platform

from pathlib import Path
from typing import List, Awaitable

from il2fb.config.ds import ServerConfig


LOG = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "confs.ini"
DEFAULT_START_SCRIPT_NAME = "server.cmd"


def _try_to_normalize_exe_path(initial: str) -> Path:
    path = Path(initial).resolve()

    if not os.access(path, os.F_OK):
        raise FileNotFoundError(
            f"dedicated server's executable does not exist (path='{path}')"
        )

    if not os.access(path, os.X_OK):
        raise PermissionError(
            f"dedicated server's executable cannot be executed (path='{path}')"
        )

    return path


def _try_to_normalize_config_path(
    root_dir: Path,
    initial: str=None,
    default_name: str=DEFAULT_CONFIG_NAME,
) -> Path:

    if initial is None:
        path = root_dir / default_name
    elif os.path.sep in initial:
        path = Path(initial).resolve()
    else:
        path = root_dir / initial

    if not os.access(path, os.F_OK):
        raise FileNotFoundError(
            f"dedicated server's config does not exist (path='{path}')"
        )

    if not os.access(path, os.R_OK):
        raise PermissionError(
            f"dedicated server's config cannot be read (path='{path}')"
        )

    return path


def _try_to_normalize_start_script_path(
    root_dir: Path,
    initial: str=None,
    default_name: str=DEFAULT_START_SCRIPT_NAME,
) -> Path:

    if initial is None:
        path = root_dir / default_name
    elif os.path.sep in initial:
        path = Path(initial).resolve()
    else:
        path = root_dir / initial

    if not os.access(path, os.F_OK):
        raise FileNotFoundError(
            f"dedicated server's start script does not exist (path='{path}')"
        )

    if not os.access(path, os.R_OK):
        raise PermissionError(
            f"dedicated server's start script cannot be read (path='{path}')"
        )

    return path


def _try_to_load_config(path: str) -> ServerConfig:
    ini = configparser.ConfigParser()
    ini.read(path)
    return ServerConfig.from_ini(ini)


def _try_to_handle_stream(handler, s: str) -> None:
    try:
        handler(s)
    except Exception:
        LOG.exception(f"failed to handle dedicated server's stream '{s}'")


def _is_eol(char: str) -> bool:
    return char == '\n'


def _is_prompt(char: str, chars: List[str]) -> bool:
    if char != '>':
        return False

    try:
        int(''.join(chars))
    except ValueError:
        return False
    else:
        return True


async def _read_stream_until_line(
    stream, stream_name, input_line, stop_line, handler=None,
) -> Awaitable:
    chars = []

    while True:
        char = await stream.read(1)

        if not char:
            raise EOFError(
                f"dedicated server's {stream_name} stream was closed "
                f"unexpectedly"
            )

        char = char.decode()
        do_flush = (_is_eol(char) or _is_prompt(char, chars))
        chars.append(char)

        if not do_flush:
            continue

        s, chars = ''.join(chars), []

        if s == stop_line:
            if handler:
                handler(input_line)
                handler(stop_line)
            return

        if handler:
            handler(s)


async def _read_stream(stream, stream_name, handler) -> Awaitable:
    chars = []

    while True:
        char = await stream.read(1)

        if not char:
            LOG.debug(f"dedicated server's {stream_name} stream was closed")
            break

        char = char.decode()
        do_flush = (_is_eol(char) or _is_prompt(char, chars))
        chars.append(char)

        if not do_flush:
            continue

        s, chars = ''.join(chars), []
        handler(s)

    if chars:
        s, chars = ''.join(chars), []
        handler(s)


class DedicatedServer:

    def __init__(
        self,
        loop,
        exe_path: str,
        config_path: str=None,
        start_script_path: str=None,
        wine_bin_path: str="wine",
        stdout_handler=None,
        stderr_handler=None,
    ):
        self._loop = loop
        self.exe_path = _try_to_normalize_exe_path(exe_path)
        self.root_dir = self.exe_path.parent
        self.config_path = _try_to_normalize_config_path(
            root_dir=self.root_dir,
            initial=config_path,
        )
        self.config = _try_to_load_config(self.config_path)
        self.start_script_path = _try_to_normalize_start_script_path(
            root_dir=self.root_dir,
            initial=start_script_path,
        )
        self._wine_bin_path = wine_bin_path
        self._stdout_handler = (
            functools.partial(_try_to_handle_stream, stdout_handler)
            if stdout_handler
            else None
        )
        self._stderr_handler = (
            functools.partial(_try_to_handle_stream, stderr_handler)
            if stderr_handler
            else None
        )
        self._process = None
        self._start_future = asyncio.Future()

    @property
    def pid(self):
        return self._process and self._process.pid

    async def run(self) -> Awaitable:
        try:
            stream_tasks = await self._start()
        except Exception as e:
            if self._process:
                self._process.kill()
                await self._process.wait()

            self._start_future.set_exception(e)
            raise e

        self._start_future.set_result(None)

        if stream_tasks:
            await asyncio.gather(*stream_tasks)

        await self._process.wait()

    async def _start(self) -> Awaitable[List[asyncio.Task]]:
        tasks = []

        await self._spawn_process()

        if self._stderr_handler:
            stream_task = self._loop.create_task(_read_stream(
                stream=self._process.stderr,
                stream_name="STDERR",
                handler=self._stderr_handler,
            ))
            tasks.append(stream_task)
        else:
            self._process.stderr.close()

        input_line = "host\n"
        stop_line = "localhost: Server\n"

        boot_task = self._loop.create_task(_read_stream_until_line(
            stream=self._process.stdout,
            stream_name="STDOUT",
            input_line=input_line,
            stop_line=stop_line,
            handler=self._stdout_handler,
        ))

        await self.input(input_line)
        await boot_task

        if self._stdout_handler:
            stream_task = self._loop.create_task(_read_stream(
                stream=self._process.stdout,
                stream_name="STDOUT",
                handler=self._stdout_handler,
            ))
            tasks.append(stream_task)
        else:
            self._process.stdout.close()

        return tasks

    async def _spawn_process(self) -> Awaitable:
        args = (
            []
            if platform.system() == 'Windows'
            else [self._wine_bin_path, ]
        )
        args.extend([
            str(self.exe_path),
            '-conf', str(self.config_path),
            '-cmd', str(self.start_script_path),
        ])
        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    def wait_for_start(self) -> Awaitable:
        return self._start_future

    async def input(self, s: str) -> Awaitable:
        self._process.stdin.write(s.encode())
        await self._process.stdin.drain()
