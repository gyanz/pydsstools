cimport cython
cimport libcpp
#
from cpython.array cimport array as carray
import array as py_array
from cpython cimport array
#
from cython cimport view,nogil
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython.unicode cimport PyUnicode_AsUTF8AndSize
from cpython.exc   cimport PyErr_NoMemory
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_FromStringAndSize
from cpython.unicode cimport PyUnicode_DecodeASCII
from libc.stdint cimport int16_t, int32_t,SIZE_MAX
from libc.stddef  cimport size_t
from libc.stdlib cimport malloc,calloc, free
from libc.string cimport strlen, memcpy
from libc.math cimport floor,ceil
#from _chelper cimport *
from checlib cimport *
import logging
logger = logging.getLogger(__name__)
import sys
from datetime import datetime,timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
#from affine import Affine
#from collections import namedtuple
import numpy as np
# NumPy 2.0 compatibility: import_array() is required for C API usage
# Cython 3.0+ handles this automatically, but explicit call ensures compatibility
cimport numpy as np
cimport numpy as cnp
np.import_array()
np.seterr(over='raise')
import re
from collections import namedtuple as _namedtuple
from pydsstools.core.enums import BinaryType