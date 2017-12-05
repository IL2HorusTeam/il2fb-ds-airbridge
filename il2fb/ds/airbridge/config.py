# coding: utf-8

import dictlib
import yaml

from ddict import DotAccessDict
from jsonschema import validate


CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'logging': {
            'type': 'object',
            'properties': {
                'trace': {
                    'type': 'boolean',
                },
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
        'state': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                },
            },
            'required': ['file_path', ],
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
                'wine_bin_path': {
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
                'is_interactive': {
                    'type': 'boolean',
                },
            },
            'required': ['exe_path', ],
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
                        'private_key_path': {
                            'type': 'string',
                        },
                        'certificate_path': {
                            'type': 'string',
                        },
                        'ca_path': {
                            'type': 'string',
                        },
                    },
                    'required': [
                        'private_key_path', 'certificate_path', 'ca_path',
                    ],
                },
            },
            'required': ['servers', ],
        },
        'api': {
            'type': 'object',
            'properties': {
                'nats': {
                    'type': 'object',
                    'properties': {
                        'subject': {
                            'type': 'string',
                        },
                    },
                    'required': ['subject', ],
                },
                'http': {
                    'type': 'object',
                    'properties': {
                        'bind': {
                            'type': 'object',
                            'properties': {
                                'address': {
                                    'format': 'string',
                                },
                                'port': {
                                    'type': 'integer',
                                    'minimum': 0,
                                    'maximum': 65535,
                                },
                            },
                            'required': ['port', ],
                        },
                        'auth': {
                            'type': 'object',
                            'properties': {
                                'token_header_name': {
                                    'format': 'string',
                                },
                                'token_storage_path': {
                                    'format': 'string',
                                },
                            },
                            'required': ['token_storage_path', ],
                        },
                        'cors': {
                            'type': 'object',
                        },
                    },
                    'required': ['bind', ],
                },
            },
        },
        'streaming': {
            'type': 'object',
            'properties': {

                'chat': {
                    'type': 'object',
                    'properties': {

                        'subscribers': {
                            'type': 'object',
                            'properties': {

                                'file': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'path': {
                                                    'type': 'string',
                                                },
                                                'encoding': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['path', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },

                                'nats': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'subject': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['subject', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },
                            },
                        },
                    },
                },

                'events': {
                    'type': 'object',
                    'properties': {

                        'subscribers': {
                            'type': 'object',
                            'properties': {

                                'file': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'path': {
                                                    'type': 'string',
                                                },
                                                'encoding': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['path', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },

                                'nats': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'subject': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['subject', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },
                            },
                        },
                    },
                },

                'not_parsed_events': {
                    'type': 'object',
                    'properties': {

                        'subscribers': {
                            'type': 'object',
                            'properties': {

                                'file': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'path': {
                                                    'type': 'string',
                                                },
                                                'encoding': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['path', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },

                                'nats': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'subject': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['subject', ],
                                        },
                                    },
                                    'required': ['args', ],
                                },
                            },
                        },
                    },
                },

                'radar': {
                    'type': 'object',
                    'properties': {

                        'request_timeout': {
                            'type': 'number',
                        },
                        'subscribers': {
                            'type': 'object',
                            'properties': {

                                'file': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'path': {
                                                    'type': 'string',
                                                },
                                                'encoding': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['path', ],
                                        },
                                        'subscription_options': {
                                            'type': 'object',
                                            'properties': {
                                                'subscription_options': {
                                                    'type': 'integer',
                                                },
                                            },
                                        },
                                    },
                                    'required': ['args', ],
                                },

                                'nats': {
                                    'type': 'object',
                                    'properties': {
                                        'args': {
                                            'type': 'object',
                                            'properties': {
                                                'subject': {
                                                    'type': 'string',
                                                },
                                            },
                                            'required': ['subject', ],
                                        },
                                        'subscription_options': {
                                            'type': 'object',
                                            'properties': {
                                                'subscription_options': {
                                                    'type': 'integer',
                                                },
                                            },
                                        },
                                    },
                                    'required': ['args', ],
                                },
                            },
                        },
                    },
                },

            },
        },
    },
    'required': ['state', 'ds', ],
}


CONFIG_DEFAULTS = {
    'logging': {
        'trace': False,
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
