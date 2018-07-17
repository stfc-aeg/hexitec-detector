from setuptools import setup, find_packages, Extension
from distutils.command.build_ext import build_ext
from distutils.command.clean import clean
from distutils import log
from distutils.errors import LibError
import versioneer

import os
import glob
import sys
import subprocess
import shlex

stub_only = False
if '--stub-only' in sys.argv:
    stub_only = True
    sys.argv.remove('--stub-only')
    
# Define the stub fem_api extension modules 
fem_api_extension_path='fem_api_extension'
fem_api_wrapper_source = os.path.join(fem_api_extension_path, 'fem_api_wrapper.c')

fem_api_stub_source_path=os.path.join(fem_api_extension_path, 'api_stub')
fem_api_stub_sources = [fem_api_wrapper_source] + [
                            os.path.join(fem_api_stub_source_path, source) for source in [
                                'femApi.cpp', 'ExcaliburFemClient.cpp', 'FemApiError.cpp']
                             ]

fem_api_stub = Extension('excalibur.fem_api_stub', 
    sources=fem_api_stub_sources,
    include_dirs=[fem_api_stub_source_path],
    define_macros=[('COMPILE_AS_STUB', None)],
)

# Add the stub to the list of extension modules to build
fem_ext_modules = [fem_api_stub]

# If the stub_only option is not set, define the full fem_api extension module and add to the list
if not stub_only:
    
    fem_api_path=os.path.join(fem_api_extension_path, 'api')
    fem_api_source_path=os.path.join(fem_api_path, 'src')
    fem_api_include_path=os.path.join(fem_api_path, 'include')
    
    fem_api_sources = [fem_api_wrapper_source] 
    
    fem_api = Extension('excalibur.fem_api',
        sources=fem_api_sources,
        include_dirs=[fem_api_include_path], 
        library_dirs=[],
        libraries=[], 
        define_macros=[],
    )

    fem_ext_modules.append(fem_api)
  
class ExcaliburBuildExt(build_ext):
    
    def run(self):

        # Precompile the API library if necessary        
        if not stub_only:
            if (self.precompile_api_library(fem_api)):
                log.info("API library {} was recompiled, forcing rebuild of extension".format(
                    fem_api.name
                ))
                if os.path.exists(self.get_ext_fullpath(fem_api.name)):
                    os.remove(self.get_ext_fullpath(fem_api.name))
           
        # Run the real build_ext command
        build_ext.run(self)
        
    def precompile_api_library(self, fem_api_ext):
        
        log.info("Pre-compiling FEM API library")

        # If BOOST_ROOT set in environment, set up so we can pass into Makefile 
        if 'BOOST_ROOT' in os.environ:
            self.boost_root = os.environ['BOOST_ROOT']
        else:
            log.warn("BOOST_ROOT is not set in environment - library compilation may be affected")
            self.boost_root = None
                    
        # Set and create object compile path
        self.build_temp_obj_path = os.path.abspath(os.path.join(self.build_temp, 'fem_api', 'obj'))
        self.makedir(self.build_temp_obj_path)
            
        # Set and create the library output path
        self.build_temp_lib_path = os.path.abspath(os.path.join(self.build_temp, 'fem_api', 'lib'))
        self.makedir(self.build_temp_lib_path)
        
        # Build a make query command and run it
        make_query_cmd = self.build_make_cmd('-q')
        make_needed = subprocess.call(shlex.split(make_query_cmd), cwd=fem_api_path)
        
        # Build the make command
        make_cmd = self.build_make_cmd()
        
        # Run the make command
        make_rc = subprocess.call(shlex.split(make_cmd), cwd=fem_api_path)
        if make_rc != 0:
            raise LibError("Pre-compilation of API library failed")
        
        # Inject the appropriate paths and libraries into the Extension configuration
        fem_api_ext.library_dirs.append(self.build_temp_lib_path)

        if self.boost_root:        
            fem_api_ext.library_dirs.append(os.path.join(self.boost_root, 'lib'))
            fem_api_ext.runtime_library_dirs.append(os.path.join(self.boost_root, 'lib'))
            
        fem_api_ext.libraries.extend(['fem_api', 'boost_thread', 'boost_system'])

        api_library_precompiled = (make_needed > 0) and (make_rc == 0)
        
        return api_library_precompiled
        
    def makedir(self, path):
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise
            
    def build_make_cmd(self, flags=''):

        make_cmd = 'make {} OBJ_DIR={} LIB_DIR={}'.format(
            flags, self.build_temp_obj_path, self.build_temp_lib_path
            )
        if self.boost_root:
            make_cmd = make_cmd + ' BOOST_ROOT={}'.format(self.boost_root)
        
        return make_cmd
        
class ExcaliburClean(clean):
    
    def run(self):

        target_path = 'excalibur'
        ext_targets = [os.path.join(target_path, lib_name) for lib_name in ['fem_api.so', 'fem_api_stub.so']]
        
        for ext_target in ext_targets:
            if os.path.exists(ext_target):
                print('removing {}'.format(ext_target))
                os.remove(ext_target)
                                   
        clean.run(self)        

merged_cmdclass = versioneer.get_cmdclass()
merged_cmdclass.update({
    'build_ext': ExcaliburBuildExt,
    'clean': ExcaliburClean,
    })

setup(
    name='excalibur',
    version=versioneer.get_version(),
    cmdclass=merged_cmdclass,
    description='EXCALIBUR detector plugin for ODIN framework',
    url='https://github.com/stfc-aeg/odin-excalibur',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    ext_modules=fem_ext_modules,
    packages=find_packages(),
    install_requires=['odin==0.2'],
    dependency_links=['https://github.com/odin-detector/odin-control/zipball/0.2#egg=odin-0.2'],
    extras_require={
      'test': ['nose', 'coverage', 'mock'],  
    },
    entry_points={
        'console_scripts': [
            'excalibur_test_app  = excalibur.client.test_app:main',
        ]
    },
)
