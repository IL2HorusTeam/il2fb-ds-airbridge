# -*- coding: utf-8 -*-

import json as _json

from functools import partial


__all__ = ('dumps', 'loads', )


class JSONEncoder(_json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'to_primitive'):
            result = obj.to_primitive()
        elif hasattr(obj, 'isoformat'):
            result = obj.isoformat()
        else:
            result = super().default(obj)

        return result


def object_decoder(obj):
    return obj


dumps = partial(_json.dumps, cls=JSONEncoder)
loads = partial(_json.loads, object_hook=object_decoder)
