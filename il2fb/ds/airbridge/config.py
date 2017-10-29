# coding: utf-8

import dictlib
import yaml

from ddict import DotAccessDict
from jsonschema import validate


CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'debug': {
            'type': 'boolean',
        },
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
                'console_proxy': {
                    'type': 'object',
                    'properties': {
                        'bind': {
                            'type': 'object',
                            'properties': {
                                'address': {
                                    'type': 'string',
                                },
                                'port': {
                                    'type': 'integer',
                                },
                            },
                            'required': ['port', ],
                        },
                    },
                    'required': ['bind', ],
                },
                'device_link_proxy': {
                    'type': 'object',
                    'properties': {
                        'bind': {
                            'type': 'object',
                            'properties': {
                                'address': {
                                    'type': 'string',
                                },
                                'port': {
                                    'type': 'integer',
                                },
                            },
                            'required': ['port', ],
                        },
                    },
                    'required': ['bind', ],
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
        'state': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                },
            },
            'required': ['file_path', ],
        },
        'nats': {
            'type': 'object',
            'properties': {
                'servers': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'minItems': 1,
                        'uniqueItems': True,
                    },
                },
                'streaming': {
                    'type': 'object',
                    'properties': {
                        'cluster_id': {
                            'type': 'string',
                        },
                        'client_id': {
                            'type': 'string',
                        },
                    },
                    'required': ['cluster_id', 'client_id', ],
                },
                'tls': {
                    'type': 'object',
                    'properties': {
                        'ca_path': {
                            'type': 'string',
                        },
                        'certificate_path': {
                            'type': 'string',
                        },
                        'private_key_path': {
                            'type': 'string',
                        },
                    },
                    'required': [
                        'ca_path', 'certificate_path', 'private_key_path',
                    ],
                },
            },
            'required': ['servers', ],
        },
        'streaming': {
            'type': 'object',
            'properties': {
                'chat': {
                    'type': 'object',
                    'properties': {
                        'file': {
                            'type': 'object',
                            'properties': {
                                'path': {
                                    'type': 'string',
                                },
                            },
                            'required': ['path', ],
                        },
                        'nats': {
                            'type': 'object',
                            'properties': {
                                'subject': {
                                    'type': 'string',
                                },
                            },
                            'required': ['subject', ],
                        },
                    },
                },
                'events': {
                    'type': 'object',
                    'properties': {
                        'file': {
                            'type': 'object',
                            'properties': {
                                'path': {
                                    'type': 'string',
                                },
                            },
                            'required': ['path', ],
                        },
                        'nats': {
                            'type': 'object',
                            'properties': {
                                'subject': {
                                    'type': 'string',
                                },
                            },
                            'required': ['subject', ],
                        },
                    },
                },
                'not_parsed_events': {
                    'type': 'object',
                    'properties': {
                        'file': {
                            'type': 'object',
                            'properties': {
                                'path': {
                                    'type': 'string',
                                },
                            },
                            'required': ['path', ],
                        },
                        'nats': {
                            'type': 'object',
                            'properties': {
                                'subject': {
                                    'type': 'string',
                                },
                            },
                            'required': ['subject', ],
                        },
                    },
                },
            },
        },
    },
    'required': ['ds', 'wine_bin_path', 'state', ],
}


CONFIG_DEFAULTS = {
    'debug': False,
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
    'state': {
        'file_path': 'airbridge.state',
    },
}


def load_config(path: str) -> DotAccessDict:
    with open(path, 'r') as f:
        config = yaml.load(f.read())

    config = dictlib.union(CONFIG_DEFAULTS, config)
    validate(config, CONFIG_SCHEMA)

    return DotAccessDict(config)
