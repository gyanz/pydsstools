import sys
import logging

py_version = sys.version_info[0:2]

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

if arch_x64:
    if py_version == (3,8):
        logging.debug('Importing core_heclib py3.8')
        from .x64.py38 import core_heclib
        from .x64.py38.core_heclib import *
    elif py_version == (3,7):
        logging.debug('Importing core_heclib py3.7')
        from .x64.py37 import core_heclib
        from .x64.py37.core_heclib import *
    elif py_version == (3,6):
        logging.debug('Importing core_heclib py3.6')
        from .x64.py36 import core_heclib
        from .x64.py36.core_heclib import *
    else:
        raise BaseException("core_heclib extension module not supported in this version of Python")

else:
    raise BaseException("Only 64 bit system supported")


del logging, sys, arch_x64
