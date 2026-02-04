"""Conversion functions between DSS v6 and v7 grid metadata.

This module provides functions to convert between the legacy v6 format
(ctypes structures) and the modern v7 format (Pydantic models), as well
as string encoding/decoding utilities for v6 binary I/O.

String Encoding in v6
---------------------
DSS v6 stores strings as arrays of int32 values. Each int32 holds 4 ASCII
characters packed in little-endian byte order:

    "HRAP" → [1347571272]
    "MM"   → [19789]

Each int32 holds 4 bytes: H(72), R(82), A(65), P(80) → 0x50415248 = 1347571272
"""

import logging
import struct
import ctypes
from typing import Optional
from ... import HecTime, DssPathName

__all__ = [
    "str_to_ints",
    "ints_to_str",
    "float32_to_int32",
    "int32_to_float32",
    "gridinfo7_to_gridinfo6",
    "gridinfo6_to_gridinfo7_dict",
]


# ============================================================================
# String Encoding/Decoding for v6 Binary Format
# ============================================================================

def str_to_ints(s: str, endian: str = "little", signed: bool = True) -> list[int]:
    """Convert ASCII string to array of int32 values.

    Strings in DSS v6 are stored as arrays of int32, with 4 ASCII characters
    packed into each int32 value. This function performs that encoding.

    Parameters
    ----------
    s : str
        ASCII string to encode.
    endian : str, optional
        Byte order: "little" or "big", default "little".
    signed : bool, optional
        If True, use signed int32; if False, use unsigned, default True.

    Returns
    -------
    list[int]
        List of int32 values representing the string.

    Examples
    --------
    >>> str_to_ints("HRAP")
    [1347571272]
    >>> str_to_ints("MM")
    [19789]
    >>> str_to_ints("PRECIPITATION")
    [1346457936, 1414676528, 1413830225, 78]

    Notes
    -----
    Empty strings are treated as a single null character for padding.
    Strings are padded to 4-byte boundaries with null bytes.
    """
    b = s.encode("ascii")
    length = len(b)
    if length == 0:
        length = 1  # Fill empty string with nulls

    ints = []
    step = 4
    pad = b"\x00"

    for i in range(0, length, step):
        chunk = b[i : i + 4]
        chunk += pad * (4 - len(chunk))  # Pad to 4 bytes

        if signed:
            if endian == "little":
                val = struct.unpack("<i", chunk)[0]
            else:
                val = struct.unpack(">i", chunk)[0]
        else:
            if endian == "little":
                val = struct.unpack("<I", chunk)[0]
            else:
                val = struct.unpack(">I", chunk)[0]

        ints.append(val)

    return ints


_ID = bytes.maketrans(b"", b"")


def ints_to_str(
    ints: list[int],
    endian: str = "little",
    encoding: str = "ascii",
    strip_trailing_nulls: bool = True,
    stop_at_first_null: bool = True,
) -> str:
    """Convert array of int32 values to ASCII string.

    Reverse of str_to_ints(). Unpacks 4 ASCII characters from each int32
    and assembles them into a string.

    Parameters
    ----------
    ints : list[int]
        List of int32 values representing a string.
    endian : str, optional
        Byte order: "little" or "big", default "little".
    encoding : str, optional
        Character encoding, default "ascii".
    strip_trailing_nulls : bool, optional
        If True, remove null padding at end, default True.
    stop_at_first_null : bool, optional
        If True, stop at first null (C-string semantics), default True.

    Returns
    -------
    str
        Decoded ASCII string.

    Examples
    --------
    >>> ints_to_str([1347571272])
    'HRAP'
    >>> ints_to_str([19789])
    'MM'
    >>> ints_to_str([1346457936, 1414676528, 1413830225, 78])
    'PRECIPITATION'

    Notes
    -----
    - Applies C-string semantics by default (stops at first null)
    - Removes non-ASCII characters (values >= 128)
    - Handles both signed and unsigned int32 values
    """
    fmt = "<I" if endian == "little" else ">I"

    b = bytearray()
    for v in ints:
        b.extend(struct.pack(fmt, v & 0xFFFFFFFF))

    # 1) Apply C-string semantics first (if requested)
    # Everything after first NUL is discarded
    if stop_at_first_null:
        i = b.find(0)
        if i != -1:
            del b[i:]

    # 2) Optionally strip trailing NUL padding
    if strip_trailing_nulls and not stop_at_first_null:
        while b and b[-1] == 0:
            b.pop()

    # 3) Drop unwanted bytes (keep only ASCII excluding NUL)
    ascii_only = bytes(b).translate(_ID, b"\x00" + bytes(range(128, 256)))

    return ascii_only.decode(encoding)


def float32_to_int32(value: float, endian: str = "<") -> int:
    """Reinterpret float32 as int32 bits.

    Parameters
    ----------
    value : float
        32-bit floating point value.
    endian : str, optional
        Endianness: '=' native, '<' little-endian, '>' big-endian.
        Default is '<'.

    Returns
    -------
    int
        Integer with same bit pattern as float.
    """
    return struct.unpack(f"{endian}i", struct.pack(f"{endian}f", value))[0]


def int32_to_float32(value: int, endian: str = "<") -> float:
    """Reinterpret int32 bits as float32.

    Parameters
    ----------
    value : int
        32-bit integer value.
    endian : str, optional
        Endianness: '=' native, '<' little-endian, '>' big-endian.
        Default is '<'.

    Returns
    -------
    float
        Float with same bit pattern as integer.
    """
    return struct.unpack(f"{endian}f", struct.pack(f"{endian}i", value))[0]


# ============================================================================
# v7 to v6 Conversion
# ============================================================================

def gridinfo7_to_gridinfo6(gridinfo7, pathname: str):
    """Convert DSS v7 GridInfo to DSS v6 format.

    Parameters
    ----------
    gridinfo7 : GridInfo or subclass
        DSS v7 grid info object (from gridinfo package).
    pathname : str
        DSS pathname (used to extract start/end times from D and E parts).

    Returns
    -------
    GridInfo6 or subclass
        DSS v6 grid info structure (ctypes object).

    Notes
    -----
    Handles conversion of:
    - Pydantic models to ctypes structures
    - GridInfo enum types to integer codes
    - Tuple coordinates to separate X/Y fields
    - String units to int32 arrays
    - Python bools to int32 values

    Some fields may be truncated if they exceed DSS v6 limits:
    - data_units: 12 characters max
    - data_source: 12 characters max (HRAP)
    - proj_units: 12 characters max (Albers)
    - range_vals/counts: 20 bins max

    Examples
    --------
    >>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
    >>> from pydsstools.core.gridinfo.v6 import gridinfo7_to_gridinfo6
    >>>
    >>> info7 = GridInfoCreate(
    ...     grid_type=GridType.hrap,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=4762.5
    ... )
    >>> pathname = "/GRID/LOC/PRECIP/01JAN2020:0000//"
    >>> info6 = gridinfo7_to_gridinfo6(info7, pathname)
    """
    from .structures import (
        GridInfo6Base,
        GridInfo6,
        HrapInfo6,
        AlbersInfo6,
        SpecifiedInfo6,
        SPECIFIED_GRID_INFO_VERSION,
    )

    grid_type = gridinfo7.get_v6_grid_type()  # enum
    grid_type = grid_type.value
    info6 = GridInfo6Base.from_grid_type(grid_type)
    info7 = gridinfo7

    # Common parameters found in all grid types
    # -----------------------------------------
    # Start and end time from DSS pathname
    path = DssPathName(pathname)
    dpart = path.dpart
    epart = path.epart

    try:
        stime = HecTime(dpart, granularity=60)
        info6.stime = stime.value()
    except:
        info6.stime = 0

    try:
        etime = HecTime(epart, granularity=60)
        info6.etime = etime.value()
    except:
        info6.etime = 0

    # data_units
    data_units = str_to_ints(info7.data_units)
    if len(data_units) > 3:
        logging.warning("data_units was truncated during conversion to grid v6")
    info6.data_units = (ctypes.c_int32 * 3)(*data_units[0:3])

    # data_type
    info6.data_type = info7.data_type.value
    info6.lower_left_x = info7.lower_left_cell[0]
    info6.lower_left_y = info7.lower_left_cell[1]
    info6.rows = info7.shape[0]
    info6.cols = info7.shape[1]
    info6.cell_size = info7.cell_size

    # Compression
    comp_method = info7.compression_method.value
    comp_base = info7.compression_base
    comp_factor = info7.compression_factor

    info6.compression_method = comp_method
    info6.compression_base = comp_base
    info6.compression_factor = comp_factor

    # Statistics
    info6.max_val = info7.max_val
    info6.min_val = info7.min_val
    info6.mean_val = info7.mean_val
    range_vals = info7.range_vals
    range_counts = info7.range_counts
    end = 0
    for i, count in enumerate(reversed(range_counts)):
        if count != 0:
            end = i
            break
    range_length = len(range_counts) - end
    range_length = min(len(range_vals), range_length, 20)
    info6.range_length = range_length
    for i in range(range_length):
        info6.range_vals[i] = info7.range_vals[i]
        info6.range_counts[i] = info7.range_counts[i]

    # Grid type-specific fields
    # -----------------------------------------

    if grid_type == 400:
        # Undefined grid
        info_flat_size = ctypes.sizeof(GridInfo6)
        info_size = 124
        info_gsize = 124

    elif grid_type == 410:
        # HRAP
        info_flat_size = ctypes.sizeof(HrapInfo6)
        info_size = 128
        info_gsize = 124

        # data_source
        data_source = str_to_ints(info7.data_source)
        if len(data_source) > 3:
            logging.warning("data_source was truncated during conversion to grid v6")
        info6.data_source = (ctypes.c_int32 * 3)(*data_source[0:3])

    elif grid_type == 420:
        # Albers
        info_flat_size = ctypes.sizeof(AlbersInfo6)
        info_size = 164
        info_gsize = 124

        # Projection parameters
        info6.proj_datum = info7.proj_datum.value
        proj_units = str_to_ints(info7.proj_units)
        if len(proj_units) > 3:
            logging.warning("proj_unit was truncated during conversion to grid v6")
        info6.proj_units = (ctypes.c_int32 * 3)(*proj_units[0:3])
        info6.lat_origin = info7.lat_0
        info6.first_parallel = info7.lat_1
        info6.sec_parallel = info7.lat_2
        info6.central_meridian = info7.lon_0
        info6.false_easting = info7.x_0
        info6.false_northing = info7.y_0
        info6.xcoord_cell0 = info7.coords_cell0[0]
        info6.ycoord_cell0 = info7.coords_cell0[1]

    elif grid_type == 430:
        # Specified
        info_flat_size = ctypes.sizeof(SpecifiedInfo6)
        info_size = 160
        info_gsize = 124

        info6.version = SPECIFIED_GRID_INFO_VERSION

        # CRS name
        crs_name = str_to_ints(info7.crs_name)
        count = len(crs_name)
        if count > 0:
            info6.crs_name = (ctypes.c_int32 * count)(*crs_name)
        info6.crs_name_length = count
        info_flat_size += count * 4

        # CRS definition
        crs = str_to_ints(info7.crs)
        count = len(crs)
        info6.crs_def_length = count
        if count > 0:
            info6.crs_def = (ctypes.c_int32 * count)(*crs)
        info_flat_size += count * 4

        # Cell zero coordinates
        info6.xcoord_cell0 = info7.coords_cell0[0]
        info6.ycoord_cell0 = info7.coords_cell0[1]

        # NoData value
        info6.nodata = info7.nodata

        # Time zone
        tzid = str_to_ints(info7.tzid)
        count = len(tzid)
        info6.tzid_length = count
        if count > 0:
            info6.tzid = (ctypes.c_int32 * count)(*tzid)
        info_flat_size += count * 4

        info6.tzoffset = info7.tzoffset
        info6.is_interval = int(info7.is_interval)
        info6.time_stamped = int(info7.time_stamped)

    info6.info_fsize = info_flat_size
    info6.info_size = info_size
    info6.info_gsize = info_gsize
    return info6


# ============================================================================
# v6 to v7 Conversion
# ============================================================================

def gridinfo6_to_gridinfo7_dict(gridinfo6) -> dict:
    """Convert DSS v6 GridInfo to v7-compatible dictionary.

    Parameters
    ----------
    gridinfo6 : GridInfo6 or subclass
        DSS v6 grid info structure (ctypes object).

    Returns
    -------
    dict
        Dictionary compatible with GridInfoCreate() factory function.

    Notes
    -----
    Handles conversion of:
    - Separate X/Y fields to tuple coordinates
    - Integer codes to GridType enum values
    - int32 arrays to Python strings
    - CRS inference from grid parameters

    Examples
    --------
    >>> from pydsstools.core.gridinfo.v6 import gridinfo6_to_gridinfo7_dict
    >>> from pydsstools.core.gridinfo import GridInfoCreate
    >>>
    >>> # Assume info6 is a GridInfo6 from C library
    >>> info7_dict = gridinfo6_to_gridinfo7_dict(info6)
    >>> info7 = GridInfoCreate(**info7_dict)
    """
    prof6 = gridinfo6.to_dict()
    grid_type = prof6["grid_type"]

    # Convert separate X/Y to tuple
    llx = prof6.pop("lower_left_x")
    lly = prof6.pop("lower_left_y")
    prof6["lower_left_cell"] = (llx, lly)

    rows = prof6.pop("rows")
    cols = prof6.pop("cols")
    prof6["shape"] = (rows, cols)

    prof6.pop("range_length")

    # Infer CRS information
    prof6["crs_name"] = gridinfo6._infer_crs_name()
    prof6["crs"] = gridinfo6._infer_crs()

    # Grid type-specific conversions
    if grid_type == 410:
        # HRAP - no special conversion needed
        pass

    if grid_type == 420:
        # Albers
        xcoord = prof6.pop("xcoord_cell0")
        ycoord = prof6.pop("ycoord_cell0")
        prof6["coords_cell0"] = (xcoord, ycoord)

    if grid_type == 430:
        # Specified
        xcoord = prof6.pop("xcoord_cell0")
        ycoord = prof6.pop("ycoord_cell0")
        prof6["coords_cell0"] = (xcoord, ycoord)

        # Remove length fields (handled automatically in v7)
        prof6.pop("version")
        prof6.pop("crs_name_length")
        prof6.pop("crs_def_length")
        prof6.pop("tzid_length")

    return prof6
