# coding: utf-8

from contextlib import contextmanager

import yaml

from ddict import DotAccessDict

from .typing import StringOrPath


class StateLoader(yaml.Loader):
    pass


def _construct_mapping(loader, node):
    loader.flatten_mapping(node)
    return DotAccessDict(loader.construct_pairs(node))


StateLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


class StateDumper(yaml.Dumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        data.items(),
    )


StateDumper.add_representer(DotAccessDict, _dict_representer)


def load_state(path: StringOrPath) -> DotAccessDict:
    try:
        with open(path, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        data = None

    return yaml.load(data, Loader=StateLoader) if data else DotAccessDict()


def save_state(state: DotAccessDict, path: StringOrPath) -> None:
    with open(path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, Dumper=StateDumper)


@contextmanager
def track_persistent_state(path: StringOrPath) -> DotAccessDict:
    state = load_state(path)
    try:
        yield state
    finally:
        save_state(state, path)
