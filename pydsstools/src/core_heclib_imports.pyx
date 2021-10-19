import logging
import sys
from libc.math cimport floor
from cpython cimport array
from cython cimport view
from checlib cimport *
from datetime import datetime,timedelta
from libc.stdlib cimport malloc, free
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from dateutil import parser
from affine import Affine
from collections import namedtuple
import numpy as np 
np.seterr(over='raise')
cimport numpy as np
cimport libcpp 
cimport cython
