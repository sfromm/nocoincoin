#!/usr/bin/env python3

import os
import sys

from nocoin import __version__, __author__, __email__

try:
    from setuptools import setup, find_packages
except ImportError:
    print("need setuptools to build")
    sys.exit(1)

setup(
    name='nocoincoin',
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'requests',
    ],
)
