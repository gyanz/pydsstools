cimport cython
cimport libcpp 
from cpython cimport array
from cython cimport view,nogil
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython.bytes cimport PyBytes_AS_STRING
from libc.stdint cimport int16_t, int32_t
from libc.stdlib cimport malloc, free
from libc.string cimport strlen
from libc.math cimport floor,ceil
from checlib cimport *
import logging
import sys
from datetime import datetime,timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
#from affine import Affine
#from collections import namedtuple
import numpy as np 
np.seterr(over='raise')
cimport numpy as np
import re