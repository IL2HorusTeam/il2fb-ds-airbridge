# coding: utf-8

import asyncio

from pydoc import locate
from typing import Any, List, Dict

from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


CLASS_NAMES_SHORTCUTS = {
    'file': 'il2fb.ds.airbridge.streaming.subscribers.file.JSONFileStreamingSink',
}


def load_subscriber(
    loop: asyncio.AbstractEventLoop,
    cls_name: str,
    params: Dict[str, Any],
) -> StreamingSubscriber:
    cls_name = str(CLASS_NAMES_SHORTCUTS.get(cls_name, cls_name))
    cls = locate(cls_name)

    if not issubclass(cls, StreamingSubscriber):
        raise ValueError(
            f"subscriber {cls} is not a subclass of {StreamingSubscriber}"
        )

    return cls(loop=loop, **params)


def load_subscribers_from_config(
    loop: asyncio.AbstractEventLoop,
    config: Dict[str, Dict[str, Any]],
) -> List[StreamingSubscriber]:
    return [
        load_subscriber(loop, cls_name, params)
        for cls_name, params in config.items()
    ]
