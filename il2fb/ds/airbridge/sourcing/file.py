# coding: utf-8

import json

from pathlib import Path
from typing import Any

from il2fb.ds.airbridge.typing import StringOrPath


class FileSink:

    def __init__(self, path: StringOrPath):
        self._path = path if isinstance(path, Path) else Path(path)
        self._stream = None
        self._stat = None
        self._open_stream()

    def _open_stream(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self._path.open('a', buffering=1)
        self._stat = self._path.lstat()

    def _maybe_reopen_stream(self):
        try:
            stat = self._path.lstat()
        except FileNotFoundError:
            stat = None

        if (
            (stat is None) or
            (stat.st_dev != self._stat.st_dev) or
            (stat.st_ino != self._stat.st_ino)
        ):
            self.close()
            self._open_stream()

    def write(self, s: str) -> None:
        self._maybe_reopen_stream()
        self._stream.write(s + '\n')
        self._stream.flush()

    def close(self):
        try:
            self._stream.flush()
        finally:
            self._stream.close()


class JSONFileSink(FileSink):

    def write(self, o: Any) -> None:
        s = json.dumps(o)
        super().write(s)
