"""Grid metadata package for HEC-DSS grid data (Version 7).

This package provides a reorganized, type-specific implementation of grid
metadata classes for HEC-DSS files. It's structured for better maintainability
and clearer separation of concerns.

Quick Start
-----------
>>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
>>>
>>> # Create HRAP grid
>>> hrap_info = GridInfoCreate(
...     grid_type=GridType.hrap,
...     data_type=DataType.per_aver,
...     shape=(100, 150),
...     cell_size=4762.5,
...     data_units="MM"
... )
>>>
>>> # Create Albers/SHG grid
>>> albers_info = GridInfoCreate(
...     grid_type=GridType.albers,
...     data_type=DataType.inst_val,
...     shape=(500, 700),
...     cell_size=2000.0,
...     min_xy=(-1500000, 500000),
...     data_units="M"
... )
>>>
>>> # Create Specified grid with custom CRS
>>> spec_info = GridInfoCreate(
...     grid_type=GridType.specified,
...     data_type=DataType.per_aver,
...     shape=(200, 300),
...     cell_size=1000.0,
...     crs="EPSG:32610",
...     crs_name="WGS84 / UTM zone 10N",
...     nodata=-9999.0,
...     data_units="MM"
... )

Grid Classes
------------
The package supports four grid information types:

* :class:`~GridInfo` - Undefined/basic grid. Generic grid without specific
  projection information.
* :class:`~HrapInfo` - HRAP (Hydrologic Rainfall Analysis Project). Polar
  stereographic projection for precipitation data. Standard cell size:
  4.7625 km at 60N.
* :class:`~AlbersInfo` - Albers Equal Area Conic. Commonly used for Standard
  Hydrologic Grid (SHG) in HEC-HMS. Default: NAD83 / Conus Albers (EPSG:5070).
* :class:`~SpecifiedInfo` - User-defined projection. Custom CRS using WKT, PROJ
  strings, or EPSG codes. Maximum flexibility for any coordinate system.

Public API
----------
* **Main Classes**: GridInfo, HrapInfo, AlbersInfo, SpecifiedInfo
* **Factory**: GridInfoCreate - Recommended way to create grid info objects
* **Enumerations**: GridType, DataType, CompressionMethod, Datum
* **Utilities**: is_undefined_grid, is_hrap_grid, is_albers_grid,
  is_specified_grid, grid_extent, grids_overlap, validate_grid_consistency
* **v6 Compatibility**: gridinfo.v6 - DSS Version 6 structures and conversion
"""

from ..enums import GridType, DataType, CompressionMethod, Datum

# Import base classes and type checkers
from .base import (
    is_undefined_grid,
    is_hrap_grid,
    is_albers_grid,
    is_specified_grid,
)

# Import concrete grid info classes
from .undefined import GridInfo
from .hrap import HrapInfo
from .albers import AlbersInfo
from .specified import SpecifiedInfo

# Import factory function
from .factory import GridInfoCreate

# Import utility functions
from .transforms import (
    #grid_extent,
    #grids_overlap,
    #validate_grid_consistency,
    minxy_from_transform_shape,
    lower_left_cell_from_minxy,
    lower_left_cell_from_transform,
)

# v6 compatibility (imported separately to avoid cluttering main namespace)
# Users can do: from pydsstools.core.gridinfo import v6

__all__ = [
    # Enumerations
    #"GridType",
    #"DataType",
    #"CompressionMethod",
    #"Datum",

    # Factory
    "GridInfoCreate",

    # Grid info classes
    "GridInfo",
    "HrapInfo",
    "AlbersInfo",
    "SpecifiedInfo",

    # Type checkers
    #"is_undefined_grid",
    #"is_hrap_grid",
    #"is_albers_grid",
    #"is_specified_grid",

    # Utilities
    #"grid_extent",
    #"grids_overlap",
    #"validate_grid_consistency",
    #"minxy_from_transform_shape",
    #"lower_left_cell_from_minxy",
    #"lower_left_cell_from_transform",

    # Subpackage
]
