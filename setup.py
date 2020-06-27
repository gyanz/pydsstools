"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from __future__ import print_function
from setuptools import setup,find_packages
from codecs import open
from os import path
from setuptools.dist import Distribution
import sys
import platform

proj_dir = path.abspath(path.dirname(__file__))

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

if not arch_x64:
    raise Exception('Only the 64-bit Python is supported')
    
def python_requires():
    os = platform.system()
    if os == 'Linux':
        return '~=3.8'
    elif os == 'Windows':
        return '~=3.6'
    else:
        raise Exception('Operating system not supported')

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

    def has_ext_modules(self):
        return True


with open(path.join(proj_dir,'README.md'), encoding='utf-8') as fid:
    long_description = fid.read()

setup(
    name='pydsstools',

    version = '1.6',

    description ='Python library to read-write HEC-DSS database file',

    long_description = long_description,

    url = '',

    author = 'Gyan Basyal',

    author_email = 'gyanBasyalz@gmail.com',


    license = 'MIT',

    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Water resources engineers :: Developers',
        'Operating System :: Windows, Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Cython',
     ],

    packages = find_packages(),


    package_data = {'':['*.txt','*.md',
                        '_lib/x86/py36/*.pyd',
                        '_lib/x86/py37/*.pyd',
                        '_lib/x86/py38/*.pyd',
                        '_lib/x86/py36/*.so',
                        '_lib/x86/py37/*.so',
                        '_lib/x86/py38/*.so',
                        '_lib/x64/py36/*.pyd',
                        '_lib/x64/py37/*.pyd',
                        '_lib/x64/py38/*.pyd',
                        '_lib/x64/py36/*.so',
                        '_lib/x64/py37/*.so',
                        '_lib/x64/py38/*.so',
                        'examples/*','LICENSE']},

    include_package_data = True,

    data_files=[],


    distclass = BinaryDistribution,

    install_requires = ['numpy>=1.16.4', 'pandas', 'affine'],

    python_requires = python_requires(),

    zip_safe = False,

    )
