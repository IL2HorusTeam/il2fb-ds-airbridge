# coding: utf-8

import io


def write_string_to_stream(stream: io.RawIOBase, s: str) -> None:
    stream.write(s)
    stream.flush()
