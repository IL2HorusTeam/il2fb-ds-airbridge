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


def _try_normalize_exe_path(initial: str) -> Path:
    path = Path(initial).resolve()

    if not os.access(path, os.F_OK):
        raise FileNotFoundError(
            f"server executable does not exist (path='{path}')"
        )

    if not os.access(path, os.X_OK):
        raise PermissionError(
            f"server executable cannot be executed (path='{path}')"
        )

    return path


def _try_normalize_config_path(
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
            f"server config does not exist (path='{path}')"
        )

    if not os.access(path, os.R_OK):
        raise PermissionError(
            f"server config cannot be read (path='{path}')"
        )

    return path


def _try_normalize_start_script_path(
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
            f"server start script does not exist (path='{path}')"
        )

    if not os.access(path, os.R_OK):
        raise PermissionError(
            f"server start script cannot be read (path='{path}')"
        )

    return path


def _try_load_config(path: str) -> ServerConfig:
    ini = configparser.ConfigParser()
    ini.read(path)
    return ServerConfig.from_ini(ini)


def _try_handle_stdout(handler, s):
    try:
        handler(s)
    except Exception:
        LOG.exception(f"failed to handle server's stdout '{s}'")


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


async def _read_stdout_until_prompt(stdout, handler=None) -> Awaitable:
    chars = []

    while True:
        char = await stdout.read(1)

        if not char:
            LOG.debug("server's stdout was closed")
            break

        char = char.decode()
        is_eol = _is_eol(char)
        is_prompt = _is_prompt(char, chars) if not is_eol else False
        chars.append(char)

        if is_prompt:
            break
        elif not is_eol:
            continue

        s, chars = ''.join(chars), []
        if handler:
            handler(s)

    if chars:
        s, chars = ''.join(chars), []
        if handler:
            handler(s)


async def _read_stdout_until_end(stdout, handler) -> Awaitable:
    chars = []

    while True:
        char = await stdout.read(1)

        if not char:
            LOG.debug("server's stdout was closed")
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
        stdout_handler=None,
    ):
        self._loop = loop
        self.exe_path = _try_normalize_exe_path(exe_path)
        self.root_dir = self.exe_path.parent
        self.config_path = _try_normalize_config_path(
            root_dir=self.root_dir,
            initial=config_path,
        )
        self.config = _try_load_config(self.config_path)
        self.start_script_path = _try_normalize_start_script_path(
            root_dir=self.root_dir,
            initial=start_script_path,
        )
        self._stdout_handler = (
            functools.partial(_try_handle_stdout, stdout_handler)
            if stdout_handler
            else None
        )
        self._process = None
        self._start_event = asyncio.Event()

    async def run(self) -> Awaitable:
        args = (
            []
            if platform.system() == 'Windows'
            else ['wine', ]
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
            stderr=None,
        )
        await _read_stdout_until_prompt(
            stdout=self._process.stdout,
            handler=self._stdout_handler,
        )
        self._start_event.set()

        if self._stdout_handler:
            await _read_stdout_until_end(
                stdout=self._process.stdout,
                handler=self._stdout_handler,
            )
        else:
            self._process.stdout.close()

        await self.wait_for_exit()

    async def request_exit(self) -> Awaitable:
        await self.input("exit")

    async def input(self, s: str) -> Awaitable:
        self._process.stdin.write(s.encode())
        await self._process.stdin.drain()

    async def wait_for_start(self) -> Awaitable:
        await self._start_event.wait()

    async def wait_for_exit(self) -> Awaitable:
        if self._process:
            await self._process.wait()
