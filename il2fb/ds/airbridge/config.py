# coding: utf-8

import dictlib
import yaml

from jsonschema import validate


CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'ds': {
            'type': 'object',
            'properties': {
                'exe_path': {
                    'type': 'string',
                },
                'config_path': {
                    'type': 'string',
                },
                'start_script_path': {
                    'type': 'string',
                },
            },
            'required': [
                'exe_path',
                'config_path',
                'start_script_path',
            ],
        },
    },
    'required': ['ds', ],
}


CONFIG_DEFAULTS = {
    'ds': {
        'config_path': 'confs.ini',
        'start_script_path': 'server.cmd',
    }
}


def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        custom = yaml.load(f.read())

    config = dictlib.union(CONFIG_DEFAULTS, custom)
    validate(config, CONFIG_SCHEMA)

    return config
