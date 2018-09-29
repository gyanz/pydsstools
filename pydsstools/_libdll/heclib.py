import ctypes
import os
import sys
import logging

__all__ = ["_heclib"]

_heclib = None

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

curdir = os.path.abspath(__file__)
libdir = os.path.abspath(os.path.join(os.path.dirname(curdir),os.pardir,'_lib'))

if arch_x64:
    dll_path = os.path.join(libdir,'x64','gheclib')

else:
    dll_path = os.path.join(libdir,'x86','gheclib')



try:
    _heclib = ctypes.cdll.LoadLibrary(dll_path)

except:
    logging.error("Error loading heclib shared library",exc_info=True)
    _heclib = None

else:
    pass

