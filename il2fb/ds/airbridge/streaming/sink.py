# coding: utf-8

import abc

from typing import Any


class StreamingSink(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def write(self, o: Any) -> None:
        pass

    def open(self) -> None:
        pass

    def wait_opened(self) -> None:
        pass

    def close(self) -> None:
        pass

    def wait_closed(self) -> None:
        pass
