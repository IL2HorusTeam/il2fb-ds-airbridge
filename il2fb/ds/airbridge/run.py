# coding: utf-8

import argparse

from pathlib import Path

from .config import load_config


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


def main():
    args = load_args()
    config = load_config(args.config_path)
