"""Specified grid type implementation and utilities.

This module provides the SpecifiedInfo class for grids with user-defined
coordinate reference systems. This is the most flexible grid type, supporting
any CRS via WKT, PROJ, or EPSG codes.
"""

from __future__ import annotations

import logging
logger = logging.getLogger(__name__)
from typing import Optional

try:
    from typing import Annotated, Literal
except ImportError:
    from typing_extensions import Annotated, Literal

from pydantic import Field, AliasChoices

from ..enums import GridType
from ..crs import crs_short_name
from .undefined import GridInfo
from .base import PairLikeFloat, GridTypeField
from .._transform import Affine

__all__ = ["SpecifiedInfo", "update_specified_coords_from_transform", "coords_of_cell0_of_specified_grid"]


class SpecifiedInfo(GridInfo):
    """Metadata for user-specified projection grid.

    Specified grids allow arbitrary coordinate reference systems defined
    via WKT, PROJ strings, or EPSG codes. This provides maximum flexibility
    for custom projections and datums.

    In addition to the parameters inherited from :class:`GridInfo`, this class
    adds CRS definition and time zone parameters.

    Examples
    --------
    Create specified grid with UTM projection:

    >>> from pydsstools.core.gridinfo import SpecifiedInfo, DataType
    >>> info = SpecifiedInfo(
    ...     grid_type=GridType.specified,
    ...     data_type=DataType.per_aver,
    ...     shape=(200, 300),
    ...     cell_size=1000.0,
    ...     crs="EPSG:32610",  # WGS84 / UTM zone 10N
    ...     crs_name="WGS84 / UTM zone 10N",
    ...     nodata=-9999.0,
    ...     min_xy=(500000, 4000000),  # UTM coordinates
    ...     data_units="MM",
    ...     tzid="America/Los_Angeles",
    ...     tzoffset=-8
    ... )

    Using factory function (recommended):

    >>> from pydsstools.core.gridinfo import GridInfoCreate
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.specified,
    ...     data_type=DataType.inst_val,
    ...     shape=(100, 150),
    ...     cell_size=500.0,
    ...     crs="EPSG:2263",  # NAD83 / New York Long Island (ftUS)
    ...     crs_name="NY Long Island",
    ...     nodata=-9999.0,
    ...     data_units="FT"
    ... )

    Update coords from transform:

    >>> transform = (1000, 0, 500000, 0, -1000, 4200000)
    >>> info = SpecifiedInfo(...)
    >>> update_specified_coords_from_transform(info, transform)

    Notes
    -----
    **MetVue Conventions:**

    HEC-MetVue uses specific conventions for specified grids:

    * lower_left_cell is always (0, 0)
    * coords_cell0 equals min_xy (lower-left corner coordinates)
    * This differs from Albers/SHG where lower_left_cell can be non-zero

    **CRS Formats Supported:**

    * **EPSG Codes**: ``"EPSG:4326"`` (WGS84 lat/lon), ``"EPSG:32610"`` (UTM zone 10N)
    * **PROJ Strings**: ``"+proj=utm +zone=10 +datum=WGS84 +units=m +no_defs"``
    * **WKT**: Full Well-Known Text representation

    **Typical Users:**

    * HEC-MetVue for custom precipitation grids
    * Projects with non-standard coordinate systems
    * International projects with local datums

    **Key Differences from Albers/SHG:**

    * coords_cell0 represents actual grid corner (not projection origin)
    * lower_left_cell is always (0,0)
    * More flexible but requires explicit CRS definition

    **Time Zone Handling:**

    * tzid should be a standard IANA time zone name
    * tzoffset is the offset from UTC in hours
    * Both can be used; tzid is preferred for DST handling

    References
    ----------
    .. [specified1] HEC-MetVue User's Manual
                    https://www.hec.usace.army.mil/confluence/metdoc/metum/3.4.0/
    .. [specified2] DSS SpecifiedGridInfo in MetVue
                    https://www.hec.usace.army.mil/confluence/metdoc/metum/3.4.0/general-information-and-tips/dss-specifiedgridinfo-in-hec-metvue
    """

    grid_type: Annotated[
        Literal[GridType.specified_time, GridType.specified],
        Field(description="Grid type for Specified grid data. Only specified and specified_time are valid.")
    ] = GridType.specified_time
    """GridType: Type of grid projection. Only ``specified`` and ``specified_time`` are valid. Default ``GridType.specified_time``."""

    crs: str = Field(
        default="",
        validation_alias=AliasChoices(
            "crs", "crs_definition", "crs_def", "srs", "srs_def"
        ),
        description="Coordinate reference system (WKT, PROJ, or EPSG code)"
    )
    """str: Coordinate reference system definition (WKT, PROJ, or EPSG code). Default ``""``."""

    crs_name: str = Field(
        default="",
        validation_alias=AliasChoices("crs_name", "crsname", "srsname"),
        description="Short CRS name or identifier"
    )
    """str: Short name or identifier for the CRS (e.g., "EPSG:26910"). Default ``""``."""

    nodata: float = Field(
        allow_inf_nan=True,
        validation_alias=AliasChoices("nodata", "null", "nulldata", "nullvalue"),
        description="NoData value for missing/invalid cells"
    )
    """float: NoData value for missing/invalid cells (can be NaN or inf). Required."""

    tzid: str = Field(
        default="",
        validation_alias=AliasChoices(
            "tzid", "timezoneID", "time_zone_id", "timezone_id"
        ),
        description="Time zone identifier (e.g., 'America/Los_Angeles')"
    )
    """str: Time zone identifier (e.g., "America/Los_Angeles", "UTC"). Default ``""``."""

    tzoffset: int = Field(
        default=0,
        ge=-24,
        le=24,
        validation_alias=AliasChoices(
            "tzoffset", "timezoneOffset", "timezone_offset", "time_zone_offset"
        ),
        description="Time zone offset from UTC in hours"
    )
    """int: Time zone offset from UTC in hours (-24 to +24). Default ``0``."""

    coords_cell0: Optional[PairLikeFloat] = Field(
        default=(0.0, 0.0),
        validation_alias=AliasChoices(
            "coords_cell0", "coordscell0", "coords0", "xy_cell0"
        ),
        description="Coordinates of southwest corner of cell (0,0)"
    )
    """tuple[float, float] or None: Coordinates of southwest corner of cell (0,0). Default ``(0.0, 0.0)``."""

    is_interval: bool = Field(
        default=True,
        validation_alias=AliasChoices("is_interval", "isinterval", "isint"),
        description="If True, timestamps represent interval end"
    )
    """bool: If True, timestamps represent interval end. Default ``True``."""

    time_stamped: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "time_stamped", "is_time_stamped", "istimestamped", "isstamped"
        ),
        description="If True, data is associated with timestamps"
    )
    """bool: If True, data is associated with timestamps. Default ``True``."""

    def _infer_crs(self) -> str:
        """Get CRS definition for specified grid.

        Returns
        -------
        str
            CRS definition (WKT, PROJ, or EPSG code).
        """
        return self.crs

    def _infer_crs_name(self) -> str:
        """Get CRS name for specified grid.

        If crs_name is not set, tries to extract from CRS definition.

        Returns
        -------
        str
            Short CRS name or identifier.
        """
        if self.crs_name:
            return self.crs_name

        # Try to extract from CRS definition
        if self.crs:
            crs_name = crs_short_name(self.crs)
            if crs_name is not None:
                return crs_name

        return ""

    def update_cell0_from_minxy(self) -> None:
        """Set coords_cell0 from min_xy.

        Following MetVue convention, coords_cell0 equals min_xy for
        specified grids.

        Raises
        ------
        ValueError
            If min_xy is not set.

        Notes
        -----
        Modifies coords_cell0 and lower_left_cell in-place.
        lower_left_cell is always set to (0, 0).
        """
        if self.min_xy is None:
            raise ValueError("min_xy must be set to update coords_cell0")

        self.coords_cell0 = self.min_xy
        self.lower_left_cell = (0, 0)
        logger.info("Updated coords_cell0 from min_xy for specified grid")

    def update_cell0_from_transform(self, transform: Affine) -> None:
        """Update coords_cell0 from affine transform.

        Parameters
        ----------
        transform : tuple
            6-element affine transform: (dx, 0, xmin, 0, dy, ymax).

        Raises
        ------
        ValueError
            If cell size in transform doesn't match gridinfo cell_size.

        Notes
        -----
        Modifies coords_cell0 and lower_left_cell in-place.
        lower_left_cell is always set to (0, 0).
        """
        dx = self.cell_size
        dx_t = transform[0]
        if abs(dx - dx_t) > 0.001:
            raise ValueError(
                f"Cell size mismatch: gridinfo={dx}, transform={dx_t}. "
                "Cannot calculate coords_cell0."
            )

        # Calculate xmin, ymin from transform
        coords_cell0 = coords_of_cell0_of_specified_grid(transform, self.shape)
        self.coords_cell0 = coords_cell0
        self.lower_left_cell = (0, 0)
        logger.info("Updated coords_cell0 from transform for specified grid")

    def normalize(self,transform: Affine = None):
        if transform is not None:
            self.update_cell0_from_transform(transform)
        else:
            self.update_cell0_from_minxy()

# ============================================================================
# Specified Grid Utility Functions
# ============================================================================

def update_specified_coords_from_transform(
    gridinfo: SpecifiedInfo,
    transform: tuple
) -> None:
    """Update coords_cell0 for specified grid from affine transform.

    This is a convenience function that calls gridinfo.update_coords_from_transform().

    Parameters
    ----------
    gridinfo : SpecifiedInfo
        Specified grid info object to update.
    transform : tuple
        6-element affine transform: (dx, 0, xmin, 0, dy, ymax).

    Raises
    ------
    ValueError
        If cell size in transform doesn't match gridinfo cell_size.

    Examples
    --------
    >>> from pydsstools.core.gridinfo import SpecifiedInfo, update_specified_coords_from_transform
    >>> info = SpecifiedInfo(
    ...     shape=(200, 300),
    ...     cell_size=1000.0,
    ...     crs="EPSG:32610",
    ...     nodata=-9999.0,
    ...     data_type=DataType.per_aver
    ... )
    >>> transform = (1000, 0, 500000, 0, -1000, 4200000)
    >>> update_specified_coords_from_transform(info, transform)
    >>> print(info.coords_cell0)
    (500000.0, 4000000.0)
    >>> print(info.lower_left_cell)
    (0, 0)

    See Also
    --------
    SpecifiedInfo.update_coords_from_transform : Instance method
    """
    gridinfo.update_cell0_from_transform(transform)


def coords_of_cell0_of_specified_grid(
    transform: tuple,
    shape: tuple[int, int]
) -> tuple[float, float]:
    """Calculate cell (0,0) coordinates for specified grid.

    Following MetVue convention, the lower-left cell is assumed as cell (0,0).
    Returns the coordinates of the southwest corner of this cell.

    Parameters
    ----------
    transform : tuple
        6-element affine transform: (dx, 0, xmin, 0, dy, ymax).
    shape : tuple[int, int]
        Grid dimensions as (rows, cols).

    Returns
    -------
    tuple[float, float]
        Coordinates (xmin, ymin) of grid lower-left corner.

    Warnings
    --------
    Logs warning if cell sizes in x and y directions differ.

    Examples
    --------
    >>> transform = (1000, 0, 500000, 0, -1000, 4200000)
    >>> shape = (200, 300)
    >>> coords = coords_of_cell0_of_specified_grid(transform, shape)
    >>> print(coords)
    (500000.0, 4000000.0)

    Notes
    -----
    Different conventions exist for cell (0,0) location. This function
    follows MetVue convention where lower-left is the origin.

    For specified grids:
    - lower_left_cell = (0, 0)
    - coords_cell0 = (xmin, ymin)

    This differs from Albers/SHG grids where:
    - coords_cell0 = projection origin (usually (0, 0))
    - lower_left_cell = calculated based on grid position

    References
    ----------
    .. [1] MetVue Specified Grid Info
           https://www.hec.usace.army.mil/confluence/metdoc/metum/3.4.0/general-information-and-tips/dss-specifiedgridinfo-in-hec-metvue
    """
    cellsize_x = transform[0]
    cellsize_y = transform[4]
    xmin = transform[2]
    ymax = transform[5]
    rows = shape[0]

    if abs(cellsize_x) != abs(cellsize_y):
        logger.warning(
            "Cell sizes in x and y differ. DSS grids should have square cells. "
            f"cellsize_x={cellsize_x}, cellsize_y={cellsize_y}"
        )

    ymin = ymax + rows * cellsize_y
    return (xmin, ymin)


