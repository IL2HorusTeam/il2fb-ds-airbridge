# coding: utf-8

import argparse
import asyncio
import functools
import logging
import platform
import sys

from pathlib import Path

from .config import load_config
from .dedicated_server import DedicatedServer
from .logging import setup_logging


LOG = logging.getLogger(__name__)


def load_args():
    parser = argparse.ArgumentParser(
        description=(
            "Wrapper of dedicated server of "
            "«IL-2 Sturmovik: Forgotten Battles»"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-c', '--config',
        dest='config_path',
        type=lambda x: Path(x).resolve(),
        default='airbridge.yml',
        help="path to config file",
    )
    return parser.parse_args()


def get_loop():
    if platform.system() == 'Windows':
        return asyncio.ProactorEventLoop()

    return asyncio.SelectorEventLoop()


def on_dedicated_server_stdout(s: str) -> None:
    sys.stdout.write(s)
    sys.stdout.flush()


def on_stdin_ready(handler):
    line = sys.stdin.readline()
    asyncio.ensure_future(handler(line))


def validate_dedicated_server_config(config) -> None:
    if not config.console.connection.port:
        raise ValueError(
            "server's console is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#console-section)"
        )

    if not config.device_link.connection.port:
        raise ValueError(
            "server's device link is disabled, please configure it to proceed "
            "(see: https://github.com/IL2HorusTeam/il2fb-ds-config#devicelink-section)"
        )


def main():
    args = load_args()
    config = load_config(args.config_path)

    setup_logging(config.logging)

    loop = get_loop()
    asyncio.set_event_loop(loop)

    try:
        ds = DedicatedServer(
            loop=loop,
            exe_path=config.ds.exe_path,
            config_path=config.ds.get('config_path'),
            start_script_path=config.ds.get('start_script_path'),
            stdout_handler=on_dedicated_server_stdout,
        )
    except Exception:
        LOG.fatal("failed to init dedicated server", exc_info=True)
        raise SystemExit(-1)

    try:
        validate_dedicated_server_config(ds.config)
    except ValueError:
        LOG.fatal("server's config is invalid", exc_info=True)
        raise SystemExit(-1)

    ds_task = loop.create_task(ds.run())
    loop.run_until_complete(ds.wait_for_start())
    loop.add_reader(sys.stdin, functools.partial(on_stdin_ready, ds.input))

    try:
        loop.run_until_complete(asyncio.gather(ds_task))
    except KeyboardInterrupt:
        LOG.info("interrupted by user")
