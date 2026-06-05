from .x64 import core_heclib
from .x64.core_heclib import *

__all__ = [
    # Root
    "core_heclib",

    # Constants
    "UNDEFINED",
    "NODATA_FLOAT",
    "NODATA_DOUBLE",
    "NODATA_NEGATIVE",
    "NODATA_TIME",

    "HRAP_WKT",
    "SHG_WKT",
    "UTM_WKT",

    "UNDEFINED_COMPRESSION_METHOD",
    "NO_COMPRESSION",
    "ZLIB_COMPRESSION",
    "PRECIP_2_BYTE",

    "UNDEFINED_PROJECTION_DATUM",
    "NAD_27",
    "NAD_83",

    "GRID_TYPE",
    "GRID_DATA_TYPE",
    "GRID_COMPRESSION_METHODS",

    #IO
    "Open",

    # Time Series
    "TimeSeriesContainer",
    "TimeSeriesStruct",  # can't use this from python directly

    # Paired Data
    "PairedDataContainer",
    "PairedDataStruct",  # can't use this from python directly

    # Array
    "ArrayContainer",
    "ArrayStruct",

    # Text
    "TextContainer",
    "TextStruct",

    # Binary
    "BinaryStruct",
    "BinaryContainer",

    # Gridded Data
    "SpatialGridStruct",
    "GRID_DATA_TYPE",
    "GRID_COMPRESSION_METHODS",

    # Catalog
    "CatalogStruct",
    "get_pathname_catalog",
    "delete_pathname",

    # Time
    "HecTime",

    # Logging and Exceptions
    "DssLastError",
    "set_message_level",
    "get_message_level",
    "set_program_name",
    "heclib_version",
    "DssStatusException",
    "GranularityException",
    "ArgumentException",

    # Utilities
    "DssPathName",
    "vdi_from_location",
    "dss_info",
    "pd_size",
    "squeeze_file",
    "copy_record_to",
    "rename_pathname",
    "get_grid_version",
    "copy_file",
    "copy_file_to",
    "convert_version",
    "check_file",
]

