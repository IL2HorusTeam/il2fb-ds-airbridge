# coding: utf-8

from pydoc import locate

from il2fb.ds.airbridge.streaming.sinks import (
    StreamingSink, JointStreamingSink,
)


CLASS_NAMES_SHORTCUTS = {
    'file': 'il2fb.ds.airbridge.streaming.file.JSONFileStreamingSink',
}


def get_subscriber(cls_name, params) -> StreamingSink:
    cls_name = str(CLASS_NAMES_SHORTCUTS.get(cls_name, cls_name))
    cls = locate(cls_name)

    if not issubclass(cls, StreamingSink):
        raise ValueError(
            f"subscriber {cls} is not a subclass of {StreamingSink}"
        )

    return cls(**params)


def get_joint_subscriber(loop, config: dict) -> JointStreamingSink:
    items = [
        get_subscriber(cls_name, params)
        for cls_name, params in config.items()
    ]
    return JointStreamingSink(loop=loop, items=items)
