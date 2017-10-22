# coding: utf-8

import datetime

from typing import Any

from il2fb.commons.structures import BaseStructure


class TimestampedData(BaseStructure):
    __slots__ = ['timestamp', 'data', ]

    def __init__(self, data: Any):
        self.timestamp = datetime.datetime.utcnow()
        self.data = data

    def __repr__(self):
        return (
            "<TimestampedData {0}@{1}>"
            .format(
                repr(self.data),
                self.timestamp.isoformat(),
            )
        )
