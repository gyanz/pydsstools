"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import Command, Extension, setup, find_packages
from setuptools.command.build_ext import build_ext
import os
from os.path import join 
import sys
import platform
from subprocess import call
import shutil
import numpy

try:
    from Cython.Build import cythonize
    _CYTHON_INSTALLED = True
except:
    _CYTHON_INSTALLED = False

setup_dir = os.path.abspath(os.path.dirname(__file__))
print('setup directory: %r'%setup_dir)

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

if not arch_x64:
    raise Exception('Only the 64-bit Python is supported')

def is_platform_windows():
    return sys.platform == "win32" or sys.platform == "cygwin"

def is_platform_mac():
    return sys.platform == "darwin"    

def is_platform_linux():
    return sys.platform == "linux"    

def maybe_cythonize(extensions, *args, **kwargs):
    """
    Function derived from Pandas Project. This skips cythonize for the following commands
    * clean
    * sdist
    """
    if "clean" in sys.argv or "sdist" in sys.argv:
        # See https://github.com/cython/cython/issues/1495
        return extensions

    elif not _CYTHON_INSTALLED:
        raise RuntimeError("Cannot cythonize without Cython installed.")

    return cythonize(extensions, *args, **kwargs)

class CleanCommand(Command):
    """Custom command to clean the ext and build files derived from Pandas project"""

    user_options = [('all', 'a', '')]

    def initialize_options(self):
        self.all = True
        self._clean_me = [ join('pydsstools', 'src', 'core_heclib.c'),
                          join('pydsstools', 'heclib', 'dsslog.dss'),
                         ]
        self._clean_trees = [join('pydsstools', 'src', 'external', 'gridv6', 'x64'),
                            join('pydsstools', 'src', 'external', 'gridv6', 'build')
                            ]

        self._clean_exclude = []
        self._clean_exclude_dirs = [join('pydsstools', 'src', 'external', 'dss'),
                                    join('pydsstools', 'src', 'external', 'zlib'),
                                   ]

        # source
        for root, dirs, files in os.walk("pydsstools"):
            if root in self._clean_exclude_dirs:
                continue

            for d in dirs:
                if d == "__pycache__":
                    self._clean_trees.append(join(root, d))

            for x in self._clean_exclude_dirs:
                if x in root:
                    continue

            for f in files:
                filepath = join(root, f)
                if filepath in self._clean_exclude:
                    continue

                if os.path.splitext(f)[-1] in (
                    ".pyc",
                    ".pyo",
                    ".pyd",
                    ".o",
                ):
                    self._clean_me.append(filepath)
        # build
        for d in ("build", "pydsstools.egg-info"):
            if os.path.exists(d):
                self._clean_trees.append(d)

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except OSError:
                pass
        for clean_tree in self._clean_trees:
            try:
                shutil.rmtree(clean_tree)
            except OSError:
                pass

class BuildExt(build_ext):
    def build_grid_library(self):
        if is_platform_windows():
            print('Building external library: grid.lib')
            batch_file = join(setup_dir,r'pydsstools/src/external/gridv6/build.bat ')
            call(batch_file)
        else:
            print('Building external library: grid.a')
            make_dir = join(setup_dir,r'pydsstools/src/external/gridv6')
            batch_file = join(setup_dir,r'pydsstools/src/external/gridv6/build.sh')
            with open(batch_file, 'rb') as fid:
                script = fid.read()
            print('CWD: %s'%make_dir )
            call(script, shell=True, cwd=make_dir)

    def build_extensions(self):
        self.build_grid_library()
        super().build_extensions()



# Create compiler arguments

include_dirs = []
include_dirs.append(r'pydsstools/src/external/dss/headers')
include_dirs.append(r'pydsstools/src/external/gridv6/headers')
library_dirs = []

if is_platform_windows():
    # headers
    include_dirs.append(r'pydsstools/src/external/zlib')
    # lib dirs
    library_dirs.append(r'pydsstools/src/external/dss/win64')
    library_dirs.append(r'pydsstools/src/external/gridv6/build')
    library_dirs.append(r'pydsstools/src/external/zlib')
    # libs
    libraries = ['heclib_c_v6v7', 'heclib_f_v6v7', 'zlibstatic', 'grid']
    # extra compile args
    extra_compile_args = []
    extra_link_args = ['/NODEFAULTLIB:LIBCMT']

else:
    # lib dirs
    library_dirs.append(r'pydsstools/src/external/dss/linux64')
    library_dirs.append(r'pydsstools/src/external/gridv6/build')
    # libs
    libraries = [':heclib.a', ':grid.a','gfortran', 'pthread', 'm', 'quadmath', 'z', 'stdc++']
    # extra compile args
    extra_compile_args = []
    extra_link_args = []

include_dirs.append(numpy.get_include())

# why new api causing error C2039: 'dimensions': is not a member of 'tag PyArrayObject' ?
# macros = [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")] 

macros = []

extensions = [Extension('pydsstools._lib.x64.core_heclib', 
              sources =   [r'pydsstools/src/core_heclib.pyx'],
              include_dirs = include_dirs,
              library_dirs = library_dirs,
              libraries = libraries,
              define_macros = macros,
              extra_compile_args = extra_compile_args,
              extra_link_args = extra_link_args),
             ]

compiler_directives = {'embedsignature': True,
                       'language_level': '3',
                       'c_string_type': 'str',
                       'c_string_encoding': 'ascii'} 

setup(
    packages = find_packages(),

    package_data = {'':['examples/*', 'src/*.pyx', 'src/*.pyd']},

    ext_modules = maybe_cythonize(extensions, 
                                  compiler_directives = compiler_directives),

    cmdclass = {'clean':CleanCommand, 'build_ext': BuildExt},

    )
