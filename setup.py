# coding: utf-8

import os
import shlex

from setuptools import setup
from subprocess import check_output


__here__ = os.path.abspath(os.path.dirname(__file__))


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


README = open(os.path.join(__here__, "README.rst")).read()

CURRENT_COMMIT = get_commit_or_none()
CURRENT_BRANCH = get_branch_or_none()
STABLE_BRANCH = "master"
IS_STABLE_BRANCH = CURRENT_BRANCH == STABLE_BRANCH
BUILD_TAG = (
    f".{CURRENT_BRANCH}.{CURRENT_COMMIT}"
    if not IS_STABLE_BRANCH and CURRENT_COMMIT
    else ""
)


def split_requirements(lines):
    requirements, dependencies = [], []

    for line in lines:
        if line.startswith("-e"):
            line = line.split(' ', 1)[1]
            dependencies.append(line)
            line = line.split("#egg=", 1)[1]

        requirements.append(line)

    return requirements, dependencies


with open(os.path.join(__here__, "requirements", "dist.txt")) as f:
    REQUIREMENTS = [x.strip() for x in f]
    REQUIREMENTS = [x for x in REQUIREMENTS if x and not x.startswith('#')]
    REQUIREMENTS, DEPENDENCIES = split_requirements(REQUIREMENTS)


setup(
    name="il2fb-ds-airbridge",
    version="1.0.0",
    description=(
        "Wrapper of dedicated server of «IL-2 Sturmovik: Forgotten Battles»"
    ),
    license="MIT",
    url="https://github.com/IL2HorusTeam/il2fb-ds-airbridge",
    author="Alexander Oblovatniy",
    author_email="oblovatniy@gmail.com",
    packages=[
        "il2fb.ds.airbridge",
    ],
    namespace_packages=[
        "il2fb",
        "il2fb.ds",
    ],
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCIES,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications",
        "Topic :: Games/Entertainment :: Simulation",
    ],
    options={
        'egg_info': {
            'tag_build': BUILD_TAG,
        },
    },
)
