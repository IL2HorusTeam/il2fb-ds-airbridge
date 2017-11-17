# coding: utf-8

from pydoc import locate
from typing import Any, List, Dict, Tuple

from il2fb.ds.airbridge.streaming.subscribers.base import StreamingSubscriber


CLASS_NAMES_SHORTCUTS = {
    'file': 'il2fb.ds.airbridge.streaming.subscribers.file.JSONFileStreamingSink',
    'nats': 'il2fb.ds.airbridge.streaming.subscribers.nats.NATSStreamingSink',
}


def load_single_subscriber(
    app,
    cls_name: str,
    args: Dict[str, Any],
) -> StreamingSubscriber:

    cls_name = str(CLASS_NAMES_SHORTCUTS.get(cls_name, cls_name))
    cls = locate(cls_name)

    if not issubclass(cls, StreamingSubscriber):
        raise ValueError(
            f"subscriber {cls} is not a subclass of {StreamingSubscriber}"
        )

    return cls(app=app, **args)


def load_subscribers_with_subscription_options(
    app,
    config: Dict[str, Dict[str, Any]],
) -> List[Tuple[StreamingSubscriber, dict]]:

    return [
        (
            load_single_subscriber(app, cls_name, params.get('args', {})),
            params.get('subscription_options', {}),
        )
        for cls_name, params in config.items()
    ]
