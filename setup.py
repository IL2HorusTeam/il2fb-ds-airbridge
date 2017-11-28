# coding: utf-8

import shlex
import sys

from pathlib import Path
from setuptools import setup
from subprocess import check_output


__here__ = Path(__file__).parent.absolute()


def get_branch_or_none():
    try:
        return (
            check_output(shlex.split("git rev-parse --abbrev-ref HEAD"))
            .strip()
            .decode()
        )
    except Exception:
        pass


def get_commit_or_none():
    try:
        return (
            check_output(shlex.split("git rev-parse --short HEAD"))
            .strip()
            .decode()
        )
    except Exception:
        pass


def parse_requirements(file_path: Path):
    requirements, dependencies = [], []

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            if line.startswith("-e"):
                line = line.split(' ', 1)[1]
                dependencies.append(line)
                line = line.split("#egg=", 1)[1]
                requirements.append(line)
            elif line.startswith("-r"):
                name = Path(line.split(' ', 1)[1])
                path = file_path.parent / name
                subrequirements, subdependencies = parse_requirements(path)
                requirements.extend(subrequirements)
                dependencies.extend(subdependencies)
            else:
                requirements.append(line)

    return requirements, dependencies


README = open(__here__ / "README.rst").read()
CURRENT_COMMIT = get_commit_or_none()
CURRENT_BRANCH = get_branch_or_none()
STABLE_BRANCH = "master"
IS_STABLE_BRANCH = (CURRENT_BRANCH == STABLE_BRANCH)
BUILD_TAG = (
    f".{CURRENT_BRANCH}.{CURRENT_COMMIT}"
    if not IS_STABLE_BRANCH and CURRENT_COMMIT
    else ""
)
REQUIREMENTS_FILE_NAME = (
    "dist-windows.txt"
    if sys.platform == "win32"
    else "dist.txt"
)
REQUIREMENTS_FILE_PATH = __here__ / "requirements" / REQUIREMENTS_FILE_NAME
REQUIREMENTS, DEPENDENCIES = parse_requirements(REQUIREMENTS_FILE_PATH)


setup(
    name="il2fb-ds-airbridge",
    version="1.0.0-rc",
    description=(
        "Wrapper of dedicated server of «IL-2 Sturmovik: Forgotten Battles»"
    ),
    license="MIT",
    url="https://github.com/IL2HorusTeam/il2fb-ds-airbridge",
    author="Alexander Oblovatniy",
    author_email="oblovatniy@gmail.com",
    packages=[
        "il2fb.ds.airbridge",
        "il2fb.ds.airbridge.api",
        "il2fb.ds.airbridge.api.http",
        "il2fb.ds.airbridge.api.http.responses",
        "il2fb.ds.airbridge.api.http.views",
        "il2fb.ds.airbridge.dedicated_server",
        "il2fb.ds.airbridge.streaming",
        "il2fb.ds.airbridge.streaming.subscribers",
    ],
    namespace_packages=[
        "il2fb",
        "il2fb.ds",
    ],
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCIES,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Topic :: Communications",
        "Topic :: Games/Entertainment :: Simulation",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
    ],
    options={
        'egg_info': {
            'tag_build': BUILD_TAG,
        },
    },
    entry_points={
        'console_scripts': [
            'il2fb-ds-airbridge=il2fb.ds.airbridge.main:main',
        ],
    }
)
