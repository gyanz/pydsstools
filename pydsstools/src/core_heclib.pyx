#cython: c_string_type=str, c_string_encoding=ascii
#cython: embedsignature=True
DssTimeArray_PythonArrayType = 'l'
include "core_heclib_imports.pyx"
include "constants.pyx"
include "time_series.pyx"
include "paired_data.pyx"
include "open.pyx"
include "utils.pyx"
include "exceptions.pyx"
include "hectime.pyx"
include "grid.pyx"
include "catalog.pyx"

