# coding: utf-8

import abc

from typing import Any

from aiohttp import web

from il2fb.ds.airbridge import json


class RESTResponse(web.Response, abc.ABC):
    detail = None

    @property
    @abc.abstractmethod
    def status(self) -> int:
        """
        Status must be explicilty defined by subclasses.

        """

    def __init__(
        self,
        payload: dict=None,
        detail: Any=None,
        pretty: bool=False,
        content_type: str='application/json',
        charset: str='utf-8',
        **kwargs
    ):
        payload = payload if payload is not None else {}

        detail = detail if detail is not None else self.detail
        if detail:
            payload['detail'] = str(detail)

        indent = 2 if pretty else 0
        text = json.dumps(payload, indent=indent) + '\n'

        kwargs.setdefault('status', self.status)

        super().__init__(
            text=text,
            charset=charset,
            content_type=content_type,
            **kwargs
        )


class RESTSuccess(RESTResponse):
    status = 200


class RESTBadRequest(RESTResponse):
    status = 400
    detail = "Bad request."


class RESTNotFound(RESTBadRequest):
    status = 404
    detail = "Resource not found."


class RESTInternalServerError(RESTResponse):
    status = 500
    detail = (
        "The server encountered an unexpected condition that prevented it "
        "from fulfilling the request."
    )
