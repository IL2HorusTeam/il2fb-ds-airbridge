# coding: utf-8

import io
import logging
import threading
import time

from pathlib import Path

from .typing import StringHandler, StringOrPath


LOG = logging.getLogger(__name__)


class StopWatchdog(Exception):
    pass


class TextFileWatchdog:

    def __init__(self, path: StringOrPath, polling_period: float=0.5):
        self._path = path if isinstance(path, Path) else Path(path)
        self._polling_period = polling_period

        self._do_stop = False
        self._stop_lock = threading.Lock()

        self._subscribers = []
        self._subscribers_lock = threading.Lock()

        self._inode = None

    def subscribe(self, subscriber: StringHandler) -> None:
        with self._subscribers_lock:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: StringHandler) -> None:
        with self._subscribers_lock:
            self._subscribers.remove(subscriber)

    def stop(self) -> None:
        with self._stop_lock:
            self._do_stop = False

    def run(self) -> None:
        try:
            LOG.info(f"watchdog for text file `{self._path}` has started")
            self._try_run()
        except StopWatchdog:
            LOG.info(f"watchdog for text file `{self._path}` has stopped")
        except Exception:
            LOG.info(f"watchdog for text file `{self._path}` has terminated")
            raise

    def _try_run(self) -> None:
        while True:
            self._maybe_stop()

            try:
                self._run()
            except FileNotFoundError:
                continue

    def _run(self) -> None:
        while not self._path.exists():
            self._sleep_and_maybe_stop()

        with self._path.open(buffering=1) as f:
            self._read_lines(f)

    def _read_lines(self, f: io.TextIOWrapper) -> None:
        self._inode = self._get_inode()

        while True:
            where = f.tell()
            line = f.readline()

            if line:
                line = line.strip()
                self._handle_string(line)
            else:
                self._check_file_is_still_the_same()
                self._sleep_and_maybe_stop()
                f.seek(where)

    def _get_inode(self):
        return self._path.lstat().st_ino

    def _handle_string(self, s: str) -> None:
        with self._subscribers_lock:
            for subscriber in self._subscribers:
                try:
                    subscriber(s)
                except Exception:
                    LOG.exception(
                        f"subscriber {subscriber} failed to handle string {s}"
                    )

    def _check_file_is_still_the_same(self):
        try:
            inode = self._get_inode()
        except FileNotFoundError:
            self._inode = None
            raise

        if inode != self._inode:
            self._inode = None
            raise FileNotFoundError

    def _sleep_and_maybe_stop(self) -> None:
        time.sleep(self._polling_period)
        self._maybe_stop()

    def _maybe_stop(self) -> None:
        with self._stop_lock:
            if self._do_stop:
                raise StopWatchdog
