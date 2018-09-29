import os
import sys
import logging

#__all__ = ["core_heclib"]

core_heclib = None

arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

if arch_x64:
    from pydsstools._lib.x64 import core_heclib
    from pydsstools._lib.x64.core_heclib import *

else:
    from pydsstools._lib.x86 import core_heclib
    from pydsstools._lib.x86.core_heclib import *

del logging, os, sys, arch_x64
