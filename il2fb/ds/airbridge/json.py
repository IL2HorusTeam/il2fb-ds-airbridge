# -*- coding: utf-8 -*-

import json as _json

from functools import partial

from il2fb.commons.events import Event


__all__ = ('dumps', 'loads', )


class JSONEncoder(_json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'to_primitive'):
            cls = obj.__class__

            result = obj.to_primitive()
            result['__type__'] = f"{cls.__module__}.{cls.__name__}"

            if issubclass(cls, Event):
                result.pop('name')
                result.pop('verbose_name')

        elif hasattr(obj, 'isoformat'):
            result = obj.isoformat()
        else:
            result = super().default(obj)

        return result


def object_decoder(obj):
    return obj


dumps = partial(_json.dumps, cls=JSONEncoder)
loads = partial(_json.loads, object_hook=object_decoder)
