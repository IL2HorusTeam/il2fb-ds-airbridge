# coding: utf-8

from pathlib import Path
from typing import Callable, Optional, List, Union


IntOrNone = Optional[int]

StringProducer = Callable[[], str]
StringHandler = Callable[[str], None]
StringOrNone = Optional[str]
StringOrPath = Union[str, Path]
StringList = List[str]
