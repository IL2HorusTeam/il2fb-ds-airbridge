# coding: utf-8

import dictlib
import yaml

from ddict import DotAccessDict
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
            'required': ['exe_path', ],
        },
        'logging': {
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'object',
                    'properties': {
                        'main': {
                            'type': 'object',
                            'properties': {
                                'file_path': {
                                    'type': 'string',
                                },
                                'keep_after_restart': {
                                    'type': 'boolean',
                                },
                                'is_delayed': {
                                    'type': 'boolean',
                                },
                                'level': {
                                    'type': 'string',
                                },
                            },
                        },
                        'exceptions': {
                            'type': 'object',
                            'properties': {
                                'file_path': {
                                    'type': 'string',
                                },
                                'keep_after_restart': {
                                    'type': 'boolean',
                                },
                                'is_delayed': {
                                    'type': 'boolean',
                                },
                            },
                        },
                        'rotation': {
                            'type': 'object',
                            'properties': {
                                'is_enabled': {
                                    'type': 'boolean',
                                },
                                'max_size': {
                                    'type': 'integer',
                                },
                                'max_backups': {
                                    'type': 'integer',
                                },
                            },
                        },
                        'encoding': {
                            'type': 'string',
                        },
                        'use_local_time': {
                            'type': 'boolean',
                        },
                    },
                },
            },
        },
        'wine_bin_path': {
            'type': 'string',
        },
    },
    'required': ['ds', 'wine_bin_path', ],
}


CONFIG_DEFAULTS = {
    'logging': {
        'files': {
            'main': {
                'file_path': 'airbridge.log',
                'keep_after_restart': True,
                'is_delayed': False,
                'level': 'info',
            },
            'exceptions': {
                'file_path': 'airbridge.exc',
                'keep_after_restart': True,
                'is_delayed': False,
            },
            'rotation': {
                'is_enabled': True,
                'max_size': 10 * (2 ** 20),  # 10 MiB
                'max_backups': 10,
            },
            'encoding': 'utf8',
            'use_local_time': False,
        },
    },
    'wine_bin_path': 'wine',
}


def load_config(path: str) -> DotAccessDict:
    with open(path, 'r') as f:
        config = yaml.load(f.read())

    config = dictlib.union(CONFIG_DEFAULTS, config)
    validate(config, CONFIG_SCHEMA)

    return DotAccessDict(config)
