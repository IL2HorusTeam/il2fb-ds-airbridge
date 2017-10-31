# coding: utf-8

import configparser
import functools
import logging
import os
import subprocess
import threading

from pathlib import Path
from typing import Callable

from il2fb.config.ds import ServerConfig

from il2fb.ds.airbridge.compat import IS_WINDOWS
from il2fb.ds.airbridge.typing import IntOrNone, StringHandler, StringList


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


def _read_stream_until_line(
    stream, stream_name, input_line, stop_line, output_handler=None,
    prompt_handler=None,
) -> None:
    chars = []

    while True:
        char = stream.read(1)

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
        handler = (
            output_handler
            if is_eol
            else prompt_handler or output_handler
        )

        if s == stop_line:
            if handler:
                handler(input_line)
                handler(stop_line)
            return

        if handler:
            handler(s)


def _read_stream_until_end(
    stream, stream_name, output_handler, prompt_handler=None,
):
    chars = []

    while True:
        char = stream.read(1)

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


def _run_with_start_guard(start_event, target):
    start_event.set()
    target()


class DedicatedServer:

    def __init__(
        self,
        exe_path: str,
        config_path: str=None,
        start_script_path: str=None,
        wine_bin_path: str="wine",
        stdout_handler: StringHandler=None,
        stderr_handler: StringHandler=None,
        prompt_handler: StringHandler=None,
        exit_cb: Callable[[], None]=None,
    ):
        self.exe_path = _try_to_normalize_exe_path(exe_path)
        self.root_dir = self.exe_path.parent
        self.start_script_path = _try_to_normalize_start_script_path(
            root_dir=self.root_dir,
            initial=start_script_path,
        )
        self._wine_bin_path = wine_bin_path

        self.config_path = _try_to_normalize_config_path(
            root_dir=self.root_dir,
            initial=config_path,
        )
        self.config = _try_to_load_config(self.config_path)

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
        self._exit_cb = exit_cb

        self._thread = None
        self._process = None
        self._stream_handling_threads = []
        self._start_event = threading.Event()
        self._start_error = None

    @property
    def pid(self) -> IntOrNone:
        return self._process and self._process.pid

    def start(self) -> None:
        LOG.info("start dedicated server")

        if self._thread:
            raise RuntimeError("dedicated server is already started")

        self._thread = threading.Thread(target=self._run, daemon=True)

        self._start_event.clear()
        self._thread.start()
        self._start_event.wait()

        if self._start_error:
            raise self._start_error

    def _run(self) -> None:
        try:
            self._spawn_process()
            self._maybe_setup_stderr_handler()
            self._wait_started()
            self._maybe_setup_stdout_handler()
        except Exception as e:
            if self._process:
                self._process.kill()
                self._process.wait()

            self._start_error = e
        finally:
            self._start_event.set()

        self._process.wait()

        if self._exit_cb:
            try:
                self._exit_cb()
            except Exception:
                LOG.exception(
                    "failed to call exit callback of dedicated server"
                )

    def _spawn_process(self) -> None:
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
        self._process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _maybe_setup_stderr_handler(self):
        if self._stderr_handler:
            target = functools.partial(
                _read_stream_until_end,
                stream=self._process.stderr,
                stream_name="STDERR",
                output_handler=self._stderr_handler,
            )

            start_event = threading.Event()
            start_event.clear()

            thread = threading.Thread(
                target=_run_with_start_guard,
                kwargs=dict(
                    start_event=start_event,
                    target=target,
                ),
                daemon=True,
            )

            self._stream_handling_threads.append(thread)
            thread.start()
            start_event.wait()
        else:
            self._process.stderr.close()

    def _maybe_setup_stdout_handler(self):
        if self._stdout_handler:
            target = functools.partial(
                _read_stream_until_end,
                stream=self._process.stdout,
                stream_name="STDOUT",
                output_handler=self._stdout_handler,
                prompt_handler=self._prompt_handler,
            )

            start_event = threading.Event()
            start_event.clear()

            thread = threading.Thread(
                target=_run_with_start_guard,
                kwargs=dict(
                    start_event=start_event,
                    target=target,
                ),
                daemon=True,
            )

            self._stream_handling_threads.append(thread)
            thread.start()
            start_event.wait()
        else:
            self._process.stdout.close()

    def _wait_started(self) -> None:
        input_line = "host\n"
        stop_line = "localhost: Server\n"

        target = functools.partial(
            _read_stream_until_line,
            stream=self._process.stdout,
            stream_name="STDOUT",
            input_line=input_line,
            stop_line=stop_line,
            output_handler=self._stdout_handler,
            prompt_handler=self._prompt_handler,
        )

        start_event = threading.Event()
        start_event.clear()

        thread = threading.Thread(
            target=_run_with_start_guard,
            kwargs=dict(
                start_event=start_event,
                target=target,
            ),
            daemon=True,
        )
        thread.start()
        start_event.wait()

        self.input(input_line)
        thread.join()

    def input(self, s: str) -> None:
        if self._process:
            try:
                self._process.stdin.write(s.encode())
                self._process.stdin.flush()
            except Exception:
                LOG.exception(f"failed to write string to STDIN (s='{s}')")

    def ask_exit(self) -> None:
        self.input("exit\n")

    def terminate(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()

    def wait_finished(self) -> IntOrNone:
        for thread in self._stream_handling_threads:
            thread.join()

        if self._process:
            self._process.wait()
            return self._process.returncode
