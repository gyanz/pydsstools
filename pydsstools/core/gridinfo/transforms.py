"""Coordinate transformation and grid utility functions.

This module provides utilities for:
- Converting between affine transforms and grid coordinates
- Calculating grid extents
- Checking grid spatial relationships
- Validating grid consistency
"""

import logging
from math import floor
from typing import Optional, List

__all__ = [
    "minxy_from_transform_shape",
    "lower_left_cell_from_minxy",
    "lower_left_cell_from_transform",
    "grid_extent",
    "grids_overlap",
    "validate_grid_consistency",
]


# ============================================================================
# Affine Transform Utilities
# ============================================================================

def minxy_from_transform_shape(
    transform: tuple,
    shape: tuple[int, int]
) -> tuple[float, float]:
    """Calculate minimum (x, y) coordinates from affine transform and shape.

    Parameters
    ----------
    transform : tuple
        6-element affine transform: (dx, 0, xmin, 0, dy, ymax).
        dy is typically negative for north-up orientation.
    shape : tuple[int, int]
        Grid dimensions as (rows, cols).

    Returns
    -------
    tuple[float, float]
        Minimum (x, y) coordinates of grid extent.

    Warnings
    --------
    Logs warning if cell sizes in x and y directions differ.

    Examples
    --------
    >>> transform = (1000, 0, 500000, 0, -1000, 4200000)
    >>> shape = (200, 300)
    >>> minxy = minxy_from_transform_shape(transform, shape)
    >>> print(minxy)
    (500000.0, 4000000.0)

    Notes
    -----
    The transform follows GDAL convention:
    - transform[0]: pixel width (dx)
    - transform[2]: x-coordinate of upper-left corner
    - transform[4]: pixel height (dy, negative for north-up)
    - transform[5]: y-coordinate of upper-left corner
    """
    cellsize_x = transform[0]
    xmin = transform[2]
    cellsize_y = transform[4]
    ymax = transform[5]

    if abs(cellsize_x) != abs(cellsize_y):
        logging.warning(
            "Cell sizes in x and y differ. DSS grids should have square cells. "
            f"cellsize_x={cellsize_x}, cellsize_y={cellsize_y}"
        )

    rows = shape[0]
    ymin = ymax + rows * cellsize_y  # cellsize_y is negative for north-up
    return (xmin, ymin)


def lower_left_cell_from_minxy(
    minxy: tuple[float, float],
    shape: tuple[int, int],
    cellsize: float,
    xcoord_cell0: float = 0,
    ycoord_cell0: float = 0
) -> tuple[int, int]:
    """Calculate lower-left cell indices from minimum coordinates.

    Computes the cell indices for the lower-left grid cell based on
    minimum coordinates and projection origin.

    Parameters
    ----------
    minxy : tuple[float, float]
        Minimum (x, y) coordinates of grid extent.
    shape : tuple[int, int]
        Grid dimensions as (rows, cols).
    cellsize : float
        Cell size in projection units.
    xcoord_cell0 : float, optional
        X-coordinate of projection origin (false easting), default 0.
    ycoord_cell0 : float, optional
        Y-coordinate of projection origin (false northing), default 0.

    Returns
    -------
    tuple[int, int]
        Lower-left cell indices as (x_cell, y_cell).

    Examples
    --------
    For SHG/Albers grid:

    >>> minxy = (-1500000, 500000)  # In EPSG:5070 coordinates
    >>> shape = (100, 150)
    >>> cellsize = 2000.0
    >>> llc = lower_left_cell_from_minxy(minxy, shape, cellsize, 0, 0)
    >>> print(llc)
    (-750, 250)

    Notes
    -----
    Used primarily for Albers/SHG grids where the projection origin
    (xcoord_cell0, ycoord_cell0) is typically (0, 0) and different from
    the grid's actual spatial extent.

    The calculation:
    - Converts coordinates to easting/northing relative to origin
    - Divides by cell size to get cell indices
    - Uses floor() to get integer cell indices
    """
    rows = shape[0]
    xmin, ymin = minxy
    xmin_easting = xmin - xcoord_cell0
    ymin_northing = ymin - ycoord_cell0
    lower_left_x = int(floor(xmin_easting / cellsize))
    lower_left_y = int(floor(ymin_northing / cellsize))
    return (lower_left_x, lower_left_y)


def lower_left_cell_from_transform(
    transform: tuple,
    shape: tuple[int, int],
    xcoord_cell0: float = 0,
    ycoord_cell0: float = 0
) -> tuple[int, int]:
    """Calculate lower-left cell indices from affine transform.

    Parameters
    ----------
    transform : tuple
        6-element affine transform: (dx, 0, xmin, 0, dy, ymax).
    shape : tuple[int, int]
        Grid dimensions as (rows, cols).
    xcoord_cell0 : float, optional
        X-coordinate of projection origin (false easting), default 0.
    ycoord_cell0 : float, optional
        Y-coordinate of projection origin (false northing), default 0.

    Returns
    -------
    tuple[int, int]
        Lower-left cell indices as (x_cell, y_cell).

    Warnings
    --------
    Logs warning if cell sizes in x and y directions differ.

    Examples
    --------
    >>> transform = (2000, 0, -1500000, 0, -2000, 700000)
    >>> shape = (100, 150)
    >>> llc = lower_left_cell_from_transform(transform, shape, 0, 0)
    >>> print(llc)
    (-750, 250)

    See Also
    --------
    lower_left_cell_from_minxy : Calculate from coordinates
    minxy_from_transform_shape : Extract min_xy from transform

    References
    ----------
    .. [1] HEC-HMS SHG Documentation
           https://www.hec.usace.army.mil/confluence/hmsdocs/hmsum/4.8/geographic-information/coordinate-reference-systems
    """
    cellsize_x = transform[0]  # Positive for east-up
    xmin = transform[2]
    cellsize_y = transform[4]  # Negative for north-up
    ymax = transform[5]

    if abs(cellsize_x) != abs(cellsize_y):
        logging.warning(
            "Cell sizes in x and y differ. DSS grids should have square cells. "
            f"cellsize_x={cellsize_x}, cellsize_y={cellsize_y}"
        )

    rows = shape[0]
    xmin_easting = xmin - xcoord_cell0
    ymin = ymax + rows * cellsize_y
    ymin_northing = ymin - ycoord_cell0
    lower_left_x = int(floor(xmin_easting / abs(cellsize_x)))
    lower_left_y = int(floor(ymin_northing / abs(cellsize_y)))
    return (lower_left_x, lower_left_y)


# ============================================================================
# Grid Spatial Utilities
# ============================================================================

def grid_extent(gridinfo) -> tuple[float, float, float, float]:
    """Calculate geographic extent of a grid.

    Parameters
    ----------
    gridinfo : GridInfo or subclass
        Grid metadata object.

    Returns
    -------
    tuple[float, float, float, float]
        Grid extent as (xmin, ymin, xmax, ymax) in projection coordinates.

    Raises
    ------
    ValueError
        If gridinfo.min_xy is None.

    Examples
    --------
    >>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.specified,
    ...     data_type=DataType.inst_val,
    ...     shape=(200, 300),
    ...     cell_size=1000.0,
    ...     min_xy=(500000, 4000000),
    ...     crs="EPSG:32610",
    ...     nodata=-9999.0
    ... )
    >>> extent = grid_extent(info)
    >>> print(extent)
    (500000.0, 4000000.0, 800000.0, 4200000.0)

    See Also
    --------
    grids_overlap : Check if two grids overlap spatially
    """
    if gridinfo.min_xy is None:
        raise ValueError("gridinfo.min_xy must be set to calculate extent")

    xmin, ymin = gridinfo.min_xy
    rows, cols = gridinfo.shape
    cellsize = gridinfo.cell_size

    xmax = xmin + cols * cellsize
    ymax = ymin + rows * cellsize

    return (xmin, ymin, xmax, ymax)


def grids_overlap(gridinfo1, gridinfo2, tolerance: float = 0.001) -> bool:
    """Check if two grids overlap spatially.

    Parameters
    ----------
    gridinfo1 : GridInfo or subclass
        First grid metadata object.
    gridinfo2 : GridInfo or subclass
        Second grid metadata object.
    tolerance : float, optional
        Tolerance for floating point comparison, default 0.001.

    Returns
    -------
    bool
        True if grids overlap, False otherwise.

    Raises
    ------
    ValueError
        If either gridinfo has min_xy = None.

    Examples
    --------
    >>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
    >>> info1 = GridInfoCreate(
    ...     grid_type=GridType.undefined,
    ...     data_type=DataType.inst_val,
    ...     shape=(100, 100),
    ...     cell_size=1000.0,
    ...     min_xy=(0, 0)
    ... )
    >>> info2 = GridInfoCreate(
    ...     grid_type=GridType.undefined,
    ...     data_type=DataType.inst_val,
    ...     shape=(100, 100),
    ...     cell_size=1000.0,
    ...     min_xy=(50000, 50000)
    ... )
    >>> grids_overlap(info1, info2)
    True

    Notes
    -----
    This function only checks spatial overlap based on extents.
    It does not check:
    - CRS compatibility
    - Cell size compatibility
    - Grid alignment

    See Also
    --------
    grid_extent : Calculate grid extent
    """
    extent1 = grid_extent(gridinfo1)
    extent2 = grid_extent(gridinfo2)

    xmin1, ymin1, xmax1, ymax1 = extent1
    xmin2, ymin2, xmax2, ymax2 = extent2

    # Check for no overlap (with tolerance)
    if xmax1 < xmin2 - tolerance or xmax2 < xmin1 - tolerance:
        return False
    if ymax1 < ymin2 - tolerance or ymax2 < ymin1 - tolerance:
        return False

    return True


# ============================================================================
# Grid Validation Utilities
# ============================================================================

def validate_grid_consistency(gridinfo) -> List[str]:
    """Check grid metadata for common configuration errors.

    Validates:
    - Coordinate consistency (min_xy, coords_cell0, lower_left_cell)
    - Cell size reasonableness
    - Grid dimensions
    - CRS definition (for specified grids)
    - Statistics (min <= max, etc.)

    Parameters
    ----------
    gridinfo : GridInfo or subclass
        Grid metadata object to validate.

    Returns
    -------
    list[str]
        List of validation issues found. Empty list if no issues.

    Examples
    --------
    >>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.albers,
    ...     data_type=DataType.inst_val,
    ...     shape=(100, 150),
    ...     cell_size=2000.0,
    ...     min_xy=(-1500000, 500000)
    ... )
    >>> issues = validate_grid_consistency(info)
    >>> if issues:
    ...     for issue in issues:
    ...         print(f"Warning: {issue}")

    Notes
    -----
    This is a non-exhaustive validation. It catches common errors but
    may not detect all possible inconsistencies.

    See Also
    --------
    grid_extent : Calculate grid extent for spatial validation
    """
    issues = []

    # Check basic dimensions
    rows, cols = gridinfo.shape
    if rows <= 0 or cols <= 0:
        issues.append(f"Invalid grid dimensions: shape={gridinfo.shape}")

    # Check cell size
    if gridinfo.cell_size <= 0:
        issues.append(f"Invalid cell size: {gridinfo.cell_size}")
    elif gridinfo.cell_size > 1e6:
        issues.append(f"Unusually large cell size: {gridinfo.cell_size}")

    # Check statistics consistency
    if gridinfo.max_val < gridinfo.min_val:
        issues.append(
            f"max_val ({gridinfo.max_val}) < min_val ({gridinfo.min_val})"
        )

    # Check histogram consistency
    if len(gridinfo.range_vals) != len(gridinfo.range_counts):
        issues.append(
            f"range_vals length ({len(gridinfo.range_vals)}) != "
            f"range_counts length ({len(gridinfo.range_counts)})"
        )

    # Type-specific validation
    from .base import is_specified_grid, is_albers_grid

    if is_specified_grid(gridinfo.grid_type):
        # Specified grid specific checks
        if not gridinfo.crs:
            issues.append("Specified grid missing CRS definition")
        if gridinfo.lower_left_cell != (0, 0):
            issues.append(
                f"Specified grid should have lower_left_cell=(0,0), "
                f"got {gridinfo.lower_left_cell}"
            )

    if is_albers_grid(gridinfo.grid_type):
        # Albers grid specific checks
        if gridinfo.lat_1 >= gridinfo.lat_2:
            issues.append(
                f"First parallel ({gridinfo.lat_1}) should be < "
                f"second parallel ({gridinfo.lat_2})"
            )
        if not -90 <= gridinfo.lat_0 <= 90:
            issues.append(f"Invalid latitude of origin: {gridinfo.lat_0}")
        if not -180 <= gridinfo.lon_0 <= 180:
            issues.append(f"Invalid central meridian: {gridinfo.lon_0}")

    # Check coordinate consistency (if min_xy is set)
    if gridinfo.min_xy is not None:
        xmin, ymin = gridinfo.min_xy
        if hasattr(gridinfo, 'coords_cell0') and gridinfo.coords_cell0:
            x0, y0 = gridinfo.coords_cell0
            if is_albers_grid(gridinfo.grid_type):
                # For Albers, lower_left_cell should be consistent with min_xy
                if gridinfo.lower_left_cell:
                    llx, lly = gridinfo.lower_left_cell
                    expected_xmin = x0 + llx * gridinfo.cell_size
                    expected_ymin = y0 + lly * gridinfo.cell_size
                    tolerance = gridinfo.cell_size * 0.01  # 1% tolerance

                    if abs(xmin - expected_xmin) > tolerance:
                        issues.append(
                            f"Inconsistent xmin: min_xy={xmin}, "
                            f"expected from lower_left_cell={expected_xmin}"
                        )
                    if abs(ymin - expected_ymin) > tolerance:
                        issues.append(
                            f"Inconsistent ymin: min_xy={ymin}, "
                            f"expected from lower_left_cell={expected_ymin}"
                        )

    return issues
