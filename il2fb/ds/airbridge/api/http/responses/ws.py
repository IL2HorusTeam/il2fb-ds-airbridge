# coding: utf-8

from enum import IntEnum

from il2fb.ds.airbridge import json


class WS_STATUS(IntEnum):
    SUCCESS = 0
    FAILURE = 1


def WSSuccess(payload=None, detail=None):
    payload = payload or {}
    payload['status'] = WS_STATUS.SUCCESS

    if detail:
        payload['detail'] = str(detail)

    return json.dumps(payload)


def WSFailure(payload=None, detail=None):
    payload = payload or {}
    payload.update({
        'status': WS_STATUS.FAILURE,
        'detail': str(detail or "Request execution error."),
    })
    return json.dumps(payload)
