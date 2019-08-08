#cython: c_string_type=bytes, c_string_encoding=ascii
#cython: embedsignature=True
import logging
from cpython cimport array
from cython cimport view
from checlib cimport *
from datetime import datetime,timedelta
from pydsstools.heclib.util import HecTime
from pydsstools.heclib.dssExceptions import DssStatusException
try:
    import numpy as np 
except:
    np=None
cimport numpy as np 

