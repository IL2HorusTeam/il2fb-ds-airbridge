# coding: utf-8

import ssl

from ddict import DotAccessDict


def load_tls_context(
    config: DotAccessDict,
    purpose=ssl.Purpose.SERVER_AUTH,
    protocol=ssl.PROTOCOL_TLSv1_2,
) -> ssl.SSLContext:

    ctx = ssl.create_default_context(purpose=purpose)
    ctx.protocol = protocol
    ctx.load_verify_locations(config.ca_path)
    ctx.load_cert_chain(
        certfile=config.certificate_path,
        keyfile=config.private_key_path,
    )
    return ctx
