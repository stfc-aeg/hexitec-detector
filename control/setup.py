"""Setup script for Hexitec ODIN Control python package."""

# import sys
from setuptools import setup, find_packages
import versioneer
import sys
PY3 = (sys.version_info[0] == 3)

required = [
    'odin',
    # 'odin_data',  # MANUAL INSTALL REQUIRED
    'opencv-python',
    # These come from requirements.txt, but tox too myopic to see that file...
    # Seems they're no longer needed to make odin_server reg custom API adapters..
    #'nose>=1.3.7',
    #'coverage==4.1b2',
    #'codeclimate-test-reporter>=0.1.0',
    #'pyzmq>=15.2.0',
    #'requests>=2.9.1',
    #'tornado>=4.3,<5.0',
    #'future'
]

if PY3:
    required.append("matplotlib")
else:
    required.append("tornado==4.5.3")
    required.append("matplotlib<=2.9.0")
    required.append("numpy<=1.16.5")

dependency_links = [
    'https://github.com/odin-detector/odin-control/zipball/master#egg=odin'
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
      install_requires=required,
      dependency_links=dependency_links,
      zip_safe=False,
)
