""" """

import logging
from enum import Enum, IntEnum


class GridType(IntEnum):
    invalid = -9999
    undefined_time = 400
    undefined = 401
    hrap_time = 410
    hrap = 411
    albers_time = 420
    albers = 421
    specified_time = 430
    specified = 431


class DataType(IntEnum):
    invalid = -9999 # CAPI used 5
    per_aver = 0
    per_cum = 1
    inst_val = 2
    inst_cum = 3
    freq = 4


class CompressionMethod(IntEnum):
    invalid = -9999
    undefined = 0
    uncompressed = 1
    zlib = 26
    hec = 101001  # PRECIP_2_BYTE


class Datum(IntEnum):
    invalid = -9999
    undefined = 0
    nad27 = 1
    nad83 = 2


class LocCoordSystem(IntEnum):
    none = 0
    lat_long = 1
    state_plane_fips = 2
    state_plane_ads = 3
    utm = 4
    local = 5


class LocHorizUnits(IntEnum):
    unspecified = 0
    feet = 1
    meters = 2
    decimal_degrees = 3
    degrees_minutes_seconds = 4


class LocHorizDatum(IntEnum):
    unset = 0
    nad83 = 1
    nad27 = 2
    wgs84 = 3
    wgs72 = 4
    local = 5


class LocVertUnits(IntEnum):
    unspecified = 0
    feet = 1
    meters = 2


class LocVertDatum(IntEnum):
    unset = 0
    navd88 = 1
    ngvd29 = 2
    local = 3


class RegStoreFlag(IntEnum):
    replace       = 0  # always replace data
    fill_missing  = 1  # only replace missing values
    write_always  = 2  # write even if all values are missing
    skip_all_miss = 3  # if all missing, do not write and delete record if it exists
    no_overwrite  = 4  # do not allow a missing input value to replace a valid value


class IrregStoreFlag(IntEnum):
    merge   = 0  # insert new values; replace existing values at the same time
    replace = 1  # remove all data in the start-to-end range and rewrite


