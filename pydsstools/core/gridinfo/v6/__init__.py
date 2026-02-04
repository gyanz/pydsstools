"""DSS Version 6 compatibility layer.

This subpackage provides backward compatibility with DSS Version 6 grid
format. It includes ctypes structures and conversion functions.

Important
---------
This is for internal use and backward compatibility. Direct use is not
recommended. The main DSS I/O functions automatically handle v6/v7 conversion.

Submodules
----------
structures
    ctypes structures for v6 grid metadata
conversion
    Functions to convert between v6 and v7 formats

Examples
--------
Converting v7 to v6:

>>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
>>> from pydsstools.core.gridinfo.v6 import gridinfo7_to_gridinfo6
>>>
>>> # Create v7 grid info
>>> info7 = GridInfoCreate(
...     grid_type=GridType.hrap,
...     data_type=DataType.per_aver,
...     shape=(100, 150),
...     cell_size=4762.5
... )
>>>
>>> # Convert to v6 format for writing to DSS file
>>> pathname = "/GRID/LOC/PRECIP/01JAN2020:0000//"
>>> info6 = gridinfo7_to_gridinfo6(info7, pathname)

Converting v6 to v7:

>>> from pydsstools.core.gridinfo.v6 import gridinfo6_to_gridinfo7_dict
>>> from pydsstools.core.gridinfo import GridInfoCreate
>>>
>>> # Read v6 grid info from DSS file (example)
>>> info6 = ...  # GridInfo6 or subclass from C library
>>>
>>> # Convert to v7 compatible dict
>>> info7_dict = gridinfo6_to_gridinfo7_dict(info6)
>>>
>>> # Create v7 grid info
>>> info7 = GridInfoCreate(**info7_dict)

See Also
--------
gridinfo : DSS Version 7 grid metadata (preferred)
"""

from .structures import (
    GridInfo6,
    HrapInfo6,
    AlbersInfo6,
    SpecifiedInfo6,
    SPECIFIED_GRID_INFO_VERSION,
    GRIDINFO_VERSION,
)

from .conversion import (
    gridinfo7_to_gridinfo6,
    gridinfo6_to_gridinfo7_dict,
    #str_to_ints,
    #ints_to_str,
)

__all__ = [
    # Structures
    "GridInfo6",
    "HrapInfo6",
    "AlbersInfo6",
    "SpecifiedInfo6",
    "SPECIFIED_GRID_INFO_VERSION",
    "GRIDINFO_VERSION",

    # Conversion functions
    "gridinfo7_to_gridinfo6",
    "gridinfo6_to_gridinfo7_dict",
    #"str_to_ints",
    #"ints_to_str",

    # Subpackage
    #"conversion",
    #"structure"
]
