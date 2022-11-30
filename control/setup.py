"""Setup script for Hexitec ODIN Control python package."""

from setuptools import setup, find_packages
import versioneer

install_requires = [
    'odin-control @ git+https://github.com/odin-detector/odin-control@1.3.0#egg=odin_control',
    'odin-data @ git+https://github.com/odin-detector/odin-data@1.8.0#egg=odin_data&subdirectory=tools/python',
    'opencv-python==4.5.1.48',
    'pytest',
    'pytest-cov',
    'requests',
    'tox'
]

setup(name='hexitec',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Odin Detector Adapters for Hexitec',
      url='https://github.com/stfc-aeg/hexitec-detector',
      author='Christian Angelsen',
      author_email='christian.angelsen@stfc.ac.uk',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=install_requires
      )
