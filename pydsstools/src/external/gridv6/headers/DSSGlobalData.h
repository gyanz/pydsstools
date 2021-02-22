#pragma once
//#include <climits>
//#include <limits>
//
//enum RecordType1 {
//  UNKNOWN = 0, REGULAR_TIME_SERIES, REGULAR_TIME_PATTERN,
//  IRREGULAR_TIME_SERIES, IRREGULAR_TIME_PATTERN,
//  PAIRED, TEXT, SINGLE_VALUE, UNDEFINED_GRID_TYPE,
//  HRAP, ALBERS, LON_LAT, SPECIFIED_GRID_TYPE
//};

//enum DataType { PER_AVER, PER_CUM, INST_VAL, INST_CUM, FREQ, INVAL };
//enum ProjectionDatum { UNDEFINED_PROJECTION_DATUM, NAD_27, NAD_83 };
//enum CompressionMethod {
//  UNDEFINED_COMPRESSION_METHOD = 0,
//  PRECIP_2_BYTE = 101001,
//  ZLIB_DEFLATE = 26
//};

//#define UNDEFINED_INT INT_MIN
//#define UNDEFINED_FLOAT -FLT_MAX
//#ifndef MAX
//#define MAX(a,b)                ((a) > (b) ? (a) : (b))
//#endif

//#ifndef MIN
//#define MIN(a,b)                ((a) < (b) ? (a) : (b))
//#endif

/*                                                                           */
/*  NOTE: The POSIX macro INT_MAX is used to set integers as NON-INITIALIZED */
/*  NOTE: The POSIX macro DBL_MAX is used to set doubles   as NON-INITIALIZED */
/*                                                                           */

//#define UNDEFINED_INT   INT_MIN
//#define UNDEFINED_SHORT SHRT_MAX
//#define UNDEFINED_FLOAT (float) -1.0E38 //use heclib's macro
//#define UNDEFINED_DEGMINSEC -INT_MIN
//#define UNDEFINED_DOUBLE -1.0E38 //use heclib's macro

//#ifndef MIN
//#define MIN(a,b)  ((a)>(b) ? (b) : (a))
//#endif

//typedef enum { OFF, ON } OffOn;
//typedef enum { NO, true  } bool;
//
//typedef enum {
//  INFORMATION, WARNING, CRITICAL,
//  LOG_MESSAGE, LIST_MESSAGE, DIALOG_MESSAGE
//} ErrorCategory;
//
