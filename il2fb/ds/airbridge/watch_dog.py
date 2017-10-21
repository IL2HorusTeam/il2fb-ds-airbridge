# coding: utf-8

import io
import logging
import threading
import time

from pathlib import Path

from ddict import DotAccessDict

from .typing import StringHandler, StringOrPath, IntOrNone


LOG = logging.getLogger(__name__)


class StopWatchDog(Exception):
    pass


class TextFileWatchDogState(DotAccessDict):

    def __init__(self, inode: IntOrNone=None, offset: int=0):
        super().__init__(
            inode=inode,
            offset=offset,
        )

    def clear(self) -> None:
        self.inode = None
        self.offset = 0


class TextFileWatchDog:

    def __init__(
        self,
        path: StringOrPath,
        polling_period: float=0.5,
        state: TextFileWatchDogState=None,
    ):
        self._path = path if isinstance(path, Path) else Path(path)
        self._polling_period = polling_period
        self._state = state or TextFileWatchDogState()

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
        with self._stop_lock:
            self._do_stop = True

    def run(self) -> None:
        try:
            LOG.info(f"watch dog for text file `{self._path}` has started")
            self._run_with_retries()
        except StopWatchDog:
            LOG.info(f"watch dog for text file `{self._path}` has stopped")
        except Exception:
            LOG.error(f"watch dog for text file `{self._path}` has terminated")
            raise

    def _run_with_retries(self) -> None:
        while True:
            self._maybe_stop()

            try:
                self._try_to_run()
            except FileNotFoundError:
                self._state.clear()
                continue

    def _try_to_run(self) -> None:
        if self._path.exists():
            self._reset_state_if_file_was_recreated()
        else:
            self._state.clear()
            self._wait_for_file_to_get_created()

        if self._state.inode is None:
            self._state.inode = self._get_actual_inode()

        with self._path.open(buffering=1) as f:
            f.seek(self._state.offset)
            self._read_lines(f)

    def _reset_state_if_file_was_recreated(self):
        inode = self._get_actual_inode()

        if self._state.inode != inode:
            self._state.inode = inode
            self._state.offset = 0

    def _wait_for_file_to_get_created(self):
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
        inode = self._get_actual_inode()
        return (self._state.inode == inode)

    def _get_actual_inode(self) -> int:
        """
        Can raise FileNotFoundError if file does not exist.

        """
        return self._path.lstat().st_ino

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
