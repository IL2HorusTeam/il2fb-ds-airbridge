# coding: utf-8

from pydoc import locate
from typing import List

from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


CLASS_NAMES_SHORTCUTS = {
    'file': 'il2fb.ds.airbridge.streaming.subscribers.file.JSONFileStreamingSink',
}


def load_subscriber(cls_name, params) -> StreamingSubscriber:
    cls_name = str(CLASS_NAMES_SHORTCUTS.get(cls_name, cls_name))
    cls = locate(cls_name)

    if not issubclass(cls, StreamingSubscriber):
        raise ValueError(
            f"subscriber {cls} is not a subclass of {StreamingSubscriber}"
        )

    return cls(**params)


def load_subscribers_from_config(config: dict) -> List[StreamingSubscriber]:
    return [
        load_subscriber(cls_name, params)
        for cls_name, params in config.items()
    ]
