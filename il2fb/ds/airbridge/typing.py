# coding: utf-8

from pathlib import Path
from typing import Callable, Optional, List, Union

from il2fb.commons.events import Event


EventOrNone = Optional[Event]
EventHandler = Callable[[Event], None]

IntOrNone = Optional[int]

StringProducer = Callable[[], str]
StringHandler = Callable[[str], None]

StringOrNone = Optional[str]
StringOrNoneProducer = Callable[[], StringOrNone]

StringOrPath = Union[str, Path]
StringList = List[str]
