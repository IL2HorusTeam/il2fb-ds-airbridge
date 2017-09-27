# coding: utf-8

from typing import Callable, Optional, List


IntOrNone = Optional[int]

StringProducer = Callable[[], str]
StringHandler = Callable[[str], None]
StringOrNone = Optional[str]
StringList = List[str]
