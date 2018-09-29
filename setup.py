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

#install_dir = path.join(sys.prefix,'Lib','site-packages','pydsstools')

if not sys.platform.startswith('win'):
    sys.exit('Sorry only Window is supported')

if sys.version_info < (3,4) or sys.version_info >= (3,5):
    sys.exit('Sorry only Python 3.4 on Window supported')

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

    def has_ext_modules(self):
        return True


with open(path.join(proj_dir,'README.md'), encoding='utf-8') as fid:
    long_description = fid.read()

setup(
    name='pydsstools',

    version = '0.3',

    description ='Python library to read-write HEC-DSS database file',

    long_description = long_description,

    url = '',

    author = 'Gyan Basyal',

    author_email = 'gyanBasyalz@gmail.com',


    license = 'MIT',

    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Water resources engineers :: Developers',
        'Operating System :: Windows',
        'Programming Language :: Python :: 3.4',
     ],

    packages = find_packages(),


    package_data = {'':['*.txt','*.md',
                        'examples/*','LICENSE']},

    include_package_data = True,

    data_files=[],


    distclass = BinaryDistribution,

    )
