# coding: utf-8

import os

from pathlib import Path


DEFAULT_CONFIG_NAME = "confs.ini"
DEFAULT_START_SCRIPT_NAME = "server.cmd"


def normalize_exe_path(initial: str) -> Path:
    return Path(initial).resolve()


def normalize_file_path(
    root_dir: Path,
    default_name: str,
    initial: str=None,
) -> Path:

    if initial is None:
        path = root_dir / default_name
    elif os.path.sep in initial:
        path = Path(initial).resolve()
    else:
        path = root_dir / initial

    return path


def normalize_config_path(root_dir: Path, initial: str=None) -> Path:
    return normalize_file_path(
        root_dir=root_dir,
        initial=initial,
        default_name=DEFAULT_CONFIG_NAME,
    )


def normalize_start_script_path(root_dir: Path, initial: str=None) -> Path:
    return normalize_file_path(
        root_dir=root_dir,
        initial=initial,
        default_name=DEFAULT_START_SCRIPT_NAME,
    )
