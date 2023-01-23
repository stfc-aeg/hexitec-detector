"""Setup script for Hexitec ODIN Control python package."""

import sys

from setuptools import setup

import versioneer

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass()
)
