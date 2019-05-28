import os
import sys
import logging

__all__ = ['core_heclib',
           'UNDEFINED',
           'Open',
           'TimeSeriesContainer',
           'TimeSeriesStruct', #can't use this from python directly
           'PairedDataContainer',
           'PairedDataStruct', #can't use this from python directly
           'getPathnameCatalog',
           'deletePathname',
           'dss_info','HecTime',
           'SpatialGridStruct']


arch_x64 = False
if sys.maxsize > 2**32:
    arch_x64 = True

if arch_x64:
    from .._lib.x64 import core_heclib
    from .._lib.x64.core_heclib import *

else:
    from .._lib.x86 import core_heclib
    from .._lib.x86.core_heclib import *

del logging, os, sys, arch_x64


