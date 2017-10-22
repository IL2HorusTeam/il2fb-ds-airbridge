# coding: utf-8

from pathlib import Path
from typing import Awaitable, Callable, Optional, List, Union

from il2fb.commons.events import Event

from il2fb.ds.airbridge.structures import TimestampedItem


EventOrNone = Optional[Event]
EventHandler = Callable[[Event], None]

IntOrNone = Optional[int]

StringProducer = Callable[[], str]
StringHandler = Callable[[str], None]

StringOrNone = Optional[str]
StringOrNoneProducer = Callable[[], StringOrNone]

StringOrPath = Union[str, Path]
StringList = List[str]

AsyncTimestampedItemHandler = Callable[[TimestampedItem], Awaitable[None]]
