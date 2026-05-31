'''
'''
# heclib.h
# UNDEFINED_TIME -2147483647
# UNDEFINED_FLOAT -FLT_MAX
# UNDEFINED_DOUBLE -(double)FLT_MAX

# zdataTypeDescriptions.h
# Array data types (DATA_TYPE_ARRAY = 90, etc.)
ARRAY_TYPE_MIXED  = 90   # DSS-7: one record holds int + float + double together
ARRAY_TYPE_INT    = 91   # DSS-6: integer-only record
ARRAY_TYPE_FLOAT  = 92   # DSS-6: float-only record
ARRAY_TYPE_DOUBLE = 93   # DSS-6: double-only record

# Text data types (dataType field in zStructText)
# 300 covers plain text strings AND single-column text lists (numberColumns <= 1)
# 310 covers multi-column text tables (numberColumns > 1), DSS-7 only
# DSS-6 always stores dataType = 300 regardless of content
TEXT_TYPE_STRING = 300   # plain text string or text list
TEXT_TYPE_TABLE  = 310   # multi-column text table, DSS-7 only

# DATA_TYPE_UGT  400
# DATA_TYPE_UG   401
# DATA_TYPE_HGT  410
# DATA_TYPE_HG   411
# DATA_TYPE_AGT  420
# DATA_TYPE_AG   421
# DATA_TYPE_SGT  430
# DATA_TYPE_SG   431

# verticalDatum.h
# IVERTICAL_DATUM_UNSET  0
# IVERTICAL_DATUM_NAVD88 1
# IVERTICAL_DATUM_NGVD29 2
# IVERTICAL_DATUM_OTHER  3

# enum in zStructSpatialGrid.h 
UNDEFINED_PROJECTION_DATUM = 0
NAD_27 = 1
NAD_83 = 2

# zStructSpatialGrid.h (storage data type) 
GRID_FLOAT = 0 
GRID_INT = 1
GRID_DOUBLE = 2
GRID_LONG = 3

# zStructSpatialGrid.h
UNDEFINED_COMPRESSION_METHOD = 0
NO_COMPRESSION = 1
ZLIB_COMPRESSION = 26
VERSION_100 = -100
# heclibDate.h
# UNDEFINED_TIME -2147483647
# JULIAN_BASE_DATE 693960

UNDEFINED = UNDEFINED_FLOAT
NODATA_FLOAT = UNDEFINED_FLOAT
NODATA_DOUBLE = UNDEFINED_DOUBLE
NODATA_TIME = UNDEFINED_TIME
NODATA_NEGATIVE = -9999
HRAP_WKT = HRAP_SRC_DEFINITION
SHG_WKT = SHG_SRC_DEFINITION
UTM_WKT = UTM_SRC_DEFINITION
PRECIP_2_BYTE = 101001