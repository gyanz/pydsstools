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
    invalid = -9999
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


