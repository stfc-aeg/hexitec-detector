"""Setup script for Hexitec ODIN Control python package."""

import sys
from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='hexitec',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Hexitec Control',
#      url='https://github.com/stfc-aeg/odin-workshop',
      author='Christian Angelsen',
      author_email='christian.angelsen@stfc.ac.uk',
      packages=find_packages(),
      install_requires=required,
      zip_safe=False,
)
