"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup,find_packages
from codecs import open
from os import path
from setuptools.dist import Distribution
import sys

if not sys.platform.startswith('win'):
    sys.exit('Sorry only Window is supported')

if sys.version_info < (3,4) or sys.version_info >= (3,5) or sys.maxsize > 2**32:
    sys.exit('Sorry only 32-bit Python 3.4 on Window supported')  

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

    def has_ext_modules(self):
        return True

proj_dir = path.abspath(path.dirname(__file__))

with open(path.join(proj_dir,'README.md'), encoding='utf-8') as fid:
    long_description = fid.read()

setup(
    name='pydsstools',

    version = '0.2',

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


    package_data = {'':['*.txt','*.md','*.pyd','*.dll',
                    'examples/*','LICENSE']},  

    include_package_data = True,

    data_files=[],


    distclass = BinaryDistribution,  

    )
