# coding: utf-8

import io
import logging
import threading
import time

from pathlib import Path
from os import stat_result

from ddict import DotAccessDict

from il2fb.ds.airbridge.typing import StringHandler, StringOrPath


LOG = logging.getLogger(__name__)


class StopWatchDog(Exception):
    pass


class TextFileWatchDog:

    def __init__(
        self,
        path: StringOrPath,
        state: DotAccessDict=None,
        polling_period: float=0.5,
    ):
        self._path = path if isinstance(path, Path) else Path(path)
        self._state = state if state is not None else DotAccessDict()
        self._polling_period = polling_period

        self._do_stop = False
        self._stop_lock = threading.Lock()

        self._subscribers = []
        self._subscribers_lock = threading.Lock()

    def subscribe(self, subscriber: StringHandler) -> None:
        with self._subscribers_lock:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: StringHandler) -> None:
        with self._subscribers_lock:
            self._subscribers.remove(subscriber)

    def stop(self) -> None:
        LOG.debug(f"ask watch dog for text file `{self._path}` to stop")

        with self._stop_lock:
            self._do_stop = True

    def run(self) -> None:
        try:
            LOG.info(f"watch dog for text file `{self._path}` was started")
            self._run_with_retries()
        except StopWatchDog:
            LOG.info(f"watch dog for text file `{self._path}` was stopped")
        except Exception:
            LOG.error(f"watch dog for text file `{self._path}` was terminated")
            raise

    def _run_with_retries(self) -> None:
        while True:
            self._maybe_stop()

            try:
                self._try_to_run()
            except FileNotFoundError:
                self._clear_state()
                continue

    def _try_to_run(self) -> None:
        if self._path.exists():
            self._reset_state_if_file_was_recreated()
        else:
            self._clear_state()
            self._wait_for_file_to_get_created()

        if (self._state.device is None) or (self._state.inode is None):
            stat = self._get_actual_stat()
            self._state.device = stat.st_dev
            self._state.inode = stat.st_ino

        with self._path.open(buffering=1) as f:
            f.seek(self._state.offset)
            self._read_lines(f)

    def _reset_state_if_file_was_recreated(self) -> None:
        stat = self._get_actual_stat()

        if (
            (self._state.device != stat.st_dev) or
            (self._state.inode != stat.st_ino)
        ):
            self._state.device = stat.st_dev
            self._state.inode = stat.st_ino
            self._state.offset = 0

    def _clear_state(self) -> None:
        self._state.device = None
        self._state.inode = None
        self._state.offset = 0

    def _wait_for_file_to_get_created(self) -> None:
        while not self._path.exists():
            self._sleep_and_maybe_stop()

    def _read_lines(self, f: io.TextIOWrapper) -> None:
        while True:
            self._state.offset = f.tell()
            line = f.readline()

            if line:
                line = line.strip()
                self._handle_string(line)
            else:
                self._stop_if_file_was_deleted_or_recreated()
                self._sleep_and_maybe_stop()
                f.seek(self._state.offset)

    def _stop_if_file_was_deleted_or_recreated(self) -> None:
        if not self._file_is_still_the_same():
            raise FileNotFoundError

    def _file_is_still_the_same(self) -> bool:
        stat = self._get_actual_stat()
        return (
            (self._state.device == stat.st_dev) and
            (self._state.inode == stat.st_ino)
        )

    def _get_actual_stat(self) -> stat_result:
        """
        Can raise FileNotFoundError if file does not exist.

        """
        return self._path.lstat()

    def _sleep_and_maybe_stop(self) -> None:
        time.sleep(self._polling_period)
        self._maybe_stop()

    def _maybe_stop(self) -> None:
        with self._stop_lock:
            if self._do_stop:
                raise StopWatchDog

    def _handle_string(self, s: str) -> None:
        with self._subscribers_lock:
            for subscriber in self._subscribers:
                try:
                    subscriber(s)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle string "
                        f"{repr(s)}"
                    )
