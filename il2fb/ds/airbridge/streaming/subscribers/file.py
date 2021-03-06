# coding: utf-8

import logging

from pathlib import Path
from typing import Any, Awaitable

from il2fb.ds.airbridge import json
from il2fb.ds.airbridge.typing import StringOrPath
from il2fb.ds.airbridge.streaming.subscribers.base import PluggableStreamingSubscriber


LOG = logging.getLogger(__name__)


class TextFileStreamingSink(PluggableStreamingSubscriber):

    def __init__(self, app, path: StringOrPath, encoding: str='utf-8'):
        super().__init__(app=app)

        self._path = path if isinstance(path, Path) else Path(path)
        self._encoding = encoding

        self._stream = None
        self._stat = None

    def plug_in(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self._path.open(
            mode='a',
            buffering=1,  # line buffering
            encoding=self._encoding,
        )
        self._stat = self._path.lstat()

    async def write(self, s: str) -> Awaitable[None]:
        self._maybe_reopen()
        self._stream.write(s + '\n')
        self._stream.flush()

    def _maybe_reopen(self) -> None:
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
            self.open()

    def unplug(self) -> None:
        try:
            self._stream.flush()
        finally:
            self._stream.close()


class JSONFileStreamingSink(TextFileStreamingSink):

    async def write(self, o: Any) -> Awaitable[None]:
        s = json.dumps(o)
        await super().write(s)
