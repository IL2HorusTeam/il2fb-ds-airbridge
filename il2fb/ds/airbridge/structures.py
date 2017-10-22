# coding: utf-8

import datetime

from typing import Any

from il2fb.commons.structures import BaseStructure


class TimestampedItem(BaseStructure):
    __slots__ = ['timestamp', 'item', ]

    def __init__(self, item: Any):
        self.timestamp = datetime.datetime.utcnow()
        self.item = item

    def __repr__(self):
        return (
            "<TimestampedItem '{0};{1}'>"
            .format(
                self.timestamp.isoformat(),
                repr(self.item),
            )
        )
