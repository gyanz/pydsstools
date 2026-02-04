"""Albers grid type implementation and SHG utilities.

This module provides the AlbersInfo class and utilities for Standard Hydrologic
Grid (SHG) commonly used in HEC-HMS modeling. SHG uses Albers Equal Area Conic
projection with NAD83 datum.
"""

import logging
from typing import Optional

try:
    from typing import Annotated, Literal
except ImportError:
    from typing_extensions import Annotated, Literal

from pydantic import Field, AliasChoices

from ..enums import GridType, Datum, DataType
from ..crs import (
    albers as albers_crs,
    make_albers,
    albers_params_from_wkt,
    is_equal_area_conic,
    crs_short_name,
)
from .undefined import GridInfo
from .base import PairLikeFloat, GridTypeField
from .transforms import lower_left_cell_from_minxy, lower_left_cell_from_transform
from .._transform import Affine

__all__ = [
    "AlbersInfo",
    "SHG_PARAMS",
    "build_shg_gridinfo",
    "update_albers_from_crs",
]


# Standard Hydrologic Grid (SHG) default parameters (EPSG:5070)
SHG_PARAMS = {
    "proj_datum": Datum.nad83,
    "proj_units": "meter",
    "lat_0": 23.0,  # Latitude of origin
    "lat_1": 29.5,  # First standard parallel
    "lat_2": 45.5,  # Second standard parallel
    "lon_0": -96.0,  # Central meridian
    "x_0": 0.0,  # False easting
    "y_0": 0.0,  # False northing
    "coords_cell0": (0.0, 0.0),  # Origin coordinates
}


class AlbersInfo(GridInfo):
    """Metadata for Albers Equal Area Conic projection grid.

    Albers grids are commonly used for the Standard Hydrologic Grid (SHG)
    in HEC-HMS, typically using NAD83 datum with CONUS Albers parameters
    (EPSG:5070).

    In addition to the parameters inherited from :class:`GridInfo`, this class
    adds projection parameters for Albers Equal Area Conic projection.

    Examples
    --------
    Create standard SHG grid:

    >>> from pydsstools.core.gridinfo import build_shg_gridinfo, DataType
    >>> info = build_shg_gridinfo(
    ...     shape=(500, 700),
    ...     cell_size=2000.0,  # 2 km cells
    ...     min_xy=(-1500000, 500000),  # SW corner in EPSG:5070
    ...     data_type=DataType.inst_val,
    ...     data_units="M"
    ... )

    Create custom Albers grid:

    >>> from pydsstools.core.gridinfo import AlbersInfo, Datum
    >>> info = AlbersInfo(
    ...     grid_type=GridType.albers,
    ...     data_type=DataType.per_aver,
    ...     shape=(300, 400),
    ...     cell_size=5000.0,
    ...     proj_datum=Datum.nad83,
    ...     lat_0=37.0,
    ...     lat_1=34.0,
    ...     lat_2=40.5,
    ...     lon_0=-120.0,
    ...     data_units="MM"
    ... )

    Update from CRS WKT:

    >>> wkt = "PROJCS[...]"  # Full WKT string
    >>> info = AlbersInfo(...)
    >>> update_albers_from_crs(info, wkt)

    Notes
    -----
    **Albers Projection Properties:**

    * Equal-area conic projection
    * Preserves area (important for hydrologic modeling)
    * Minimizes distortion along standard parallels
    * Suitable for east-west oriented regions (e.g., CONUS)

    **Standard Hydrologic Grid (SHG) Default Parameters (EPSG:5070):**

    * Datum: NAD83
    * Units: meter
    * Origin latitude: 23.0°N
    * First parallel: 29.5°N
    * Second parallel: 45.5°N
    * Central meridian: -96.0°W
    * False easting/northing: 0, 0

    **Grid Coordinate Concepts:**

    For Albers/SHG grids, two coordinate pairs are critical:

    * **coords_cell0**: Coordinates of cell (0,0) in the global grid system.
      Usually equals (false_easting, false_northing) = (0, 0) for SHG.
      Defines the projection origin.

    * **lower_left_cell**: Cell indices of your grid's lower-left corner.
      Calculated as: ``(floor((xmin - x_0) / cellsize), floor((ymin - y_0) / cellsize))``.
      Indicates which cell in the global SHG grid corresponds to your grid origin.

    This allows multiple grid datasets to be spatially referenced in the same
    coordinate system.

    **Typical Users:**

    * HEC-HMS for watershed modeling
    * HEC-RAS for floodplain mapping
    * Hydrologic modeling in the United States

    References
    ----------
    .. [albers1] HEC-HMS Technical Reference Manual
                 https://www.hec.usace.army.mil/confluence/hmsdocs/
    .. [albers2] Standard Hydrologic Grid (SHG)
                 https://www.hec.usace.army.mil/confluence/hmsdocs/hmsum/4.8/geographic-information/coordinate-reference-systems
    """

    grid_type: Annotated[
        Literal[GridType.albers_time, GridType.albers],
        Field(description="Grid type for Albers grid data. Only albers and albers_time are valid.")
    ] = GridType.albers_time
    """GridType: Type of grid projection. Only ``albers`` and ``albers_time`` are valid. Default ``GridType.albers_time``."""

    proj_datum: Datum = Field(
        default=Datum.nad83,
        validation_alias=AliasChoices("proj_datum", "Datum", "datum"),
        description="Datum for the Albers projection"
    )
    """Datum: Datum for the projection. Default ``Datum.nad83``."""

    proj_units: str = Field(
        default="meter",
        validation_alias=AliasChoices(
            "proj_units", "pu", "proj_unit", "projection_unit", "projection_units"
        ),
        description="Linear units of the projection"
    )
    """str: Linear units of the projection. Default ``"meter"``."""

    lat_0: float = Field(
        default=23.0,
        validation_alias=AliasChoices("lat_0", "lat_origin", "lo", "latorigin", "lat0"),
        description="Latitude of projection origin (degrees)"
    )
    """float: Latitude of projection origin (degrees). Default ``23.0``."""

    lat_1: float = Field(
        default=29.5,
        validation_alias=AliasChoices(
            "lat_1", "par1", "parallel1", "lat1", "first_parallel"
        ),
        description="Latitude of first standard parallel (degrees)"
    )
    """float: Latitude of first standard parallel (degrees). Default ``29.5``."""

    lat_2: float = Field(
        default=45.5,
        validation_alias=AliasChoices(
            "lat_2",
            "second_parallel",
            "par2",
            "parallel2",
            "sec_parallel",
            "sec_par",
            "lat2",
        ),
        description="Latitude of second standard parallel (degrees)"
    )
    """float: Latitude of second standard parallel (degrees). Default ``45.5``."""

    lon_0: float = Field(
        default=-96.0,
        validation_alias=AliasChoices(
            "lon_0", "cm", "cmer", "lon0", "central_meridian"
        ),
        description="Longitude of central meridian (degrees)"
    )
    """float: Longitude of central meridian (degrees). Default ``-96.0``."""

    x_0: float = Field(
        alias="fe",
        default=0.0,
        validation_alias=AliasChoices("x_0", "x0", "fe", "false_easting"),
        description="False easting (projection units)"
    )
    """float: False easting (projection units). Default ``0.0``."""

    y_0: float = Field(
        alias="fn",
        default=0.0,
        validation_alias=AliasChoices("y_0", "y0", "fn", "false_northing"),
        description="False northing (projection units)"
    )
    """float: False northing (projection units). Default ``0.0``."""

    coords_cell0: Optional[PairLikeFloat] = Field(
        default=(0.0, 0.0),
        validation_alias=AliasChoices(
            "coords_cell0", "coordscell0", "coords0", "xy_cell0"
        ),
        description="Coordinates (easting, northing) of southwest corner of cell (0,0)"
    )
    """tuple[float, float] or None: (easting, northing) of southwest corner of cell (0,0). Default ``(0.0, 0.0)``."""

    def _infer_crs(self) -> str:
        """Infer CRS from Albers projection parameters.

        Returns
        -------
        str
            CRS definition (WKT or PROJ format).
        """
        # Check if user provided custom CRS in extra
        if "crs" in self.extra_info:
            crs = self.extra_info["crs"].strip()
            if crs:
                if not is_equal_area_conic(crs):
                    logging.warning(
                        "The provided CRS does not appear to be an equal-area "
                        "conic projection. Using it anyway, but verify it's correct."
                    )
                return crs

        # Construct CRS from projection parameters
        return make_albers(
            self.proj_datum,
            self.x_0,
            self.y_0,
            self.lon_0,
            self.lat_1,
            self.lat_2,
            self.lat_0,
        )

    def _infer_crs_name(self) -> str:
        """Infer short CRS name from Albers parameters.

        Returns
        -------
        str
            Short CRS name (e.g., "EPSG:5070" for standard SHG).
        """
        if "crs_name" in self.extra_info:
            crs_name = self.extra_info["crs_name"].strip()
            if crs_name:
                return crs_name

        # Try to get short name from CRS definition
        crs_name = crs_short_name(self._infer_crs())
        if crs_name is None:
            crs_name = "ALBERS"

        return crs_name

    def update_lower_left_cell_from_minxy(self) -> None:
        """Update lower_left_cell indices from min_xy coordinates.

        Calculates the cell indices for the lower-left corner of the grid
        based on min_xy and the projection origin (coords_cell0).

        Raises
        ------
        ValueError
            If min_xy is not set.

        Notes
        -----
        Modifies lower_left_cell in-place.
        """
        if self.min_xy is None:
            raise ValueError("min_xy must be set to calculate lower_left_cell")

        logging.info("Updating lower_left_cell indices using min_xy of Albers GridInfo")
        x_cell0, y_cell0 = self.coords_cell0
        if x_cell0 != 0.0 or y_cell0 != 0.0:
            logging.warning(
                "Normally, the grid origin coordinates in SHG/Albers (EPSG:5070) "
                "grid is (0,0). coords_cell0 is not (0,0) here."
            )

        llc = lower_left_cell_from_minxy(
            self.min_xy, self.shape, self.cell_size, x_cell0, y_cell0
        )
        self.lower_left_cell = llc

    def update_lower_left_cell_from_transform(self, transform: Affine) -> None:
        """Update lower_left_cell indices from affine transform.

        Parameters
        ----------
        transform : Affine
            6-element affine transform: (dx, 0, xmin, 0, dy, ymax).

        Raises
        ------
        ValueError
            If cell size in transform doesn't match gridinfo cell_size.

        Notes
        -----
        Modifies lower_left_cell in-place.
        """
        dx = self.cell_size
        dx_t = transform[0]
        if abs(dx - dx_t) > 0.001:
            raise ValueError(
                f"Cell size mismatch: gridinfo={dx}, transform={dx_t}. "
                "Cannot calculate lower_left_cell."
            )

        logging.info("Updating lower_left_cell indices of Albers GridInfo")
        x_cell0, y_cell0 = self.coords_cell0
        if x_cell0 != 0.0 or y_cell0 != 0.0:
            logging.warning(
                "Normally, the grid origin coordinates in SHG/Albers (EPSG:5070) "
                "grid is (0,0). coords_cell0 is not (0,0) here."
            )

        llc = lower_left_cell_from_transform(
            transform, self.shape, x_cell0, y_cell0
        )
        self.lower_left_cell = llc
    
    def update_crs_params(self, crs_wkt: str) -> None:
        update_albers_from_crs(self, crs_wkt)
    
    def normalize(self,transform: Affine = None):
        if transform is not None:
            self.update_lower_left_cell_from_transform(transform)
        else:
            self.update_lower_left_cell_from_minxy()

# ============================================================================
# Albers/SHG Utility Functions
# ============================================================================

def build_shg_gridinfo(
    shape: tuple[int, int],
    cell_size: float,
    min_xy: tuple[float, float],
    data_type: "DataType",
    data_units: str = "",
    **kwargs
) -> AlbersInfo:
    """Create a Standard Hydrologic Grid (SHG) with default parameters.

    This is a convenience function that creates an AlbersInfo with standard
    SHG parameters (NAD83 / Conus Albers, EPSG:5070).

    Parameters
    ----------
    shape : tuple[int, int]
        Grid dimensions as (rows, columns).
    cell_size : float
        Cell size in meters.
    min_xy : tuple[float, float]
        Minimum (x, y) coordinates in EPSG:5070 (meters).
    data_type : DataType
        Temporal data type.
    data_units : str, optional
        Physical units of data (e.g., "MM", "M").
    **kwargs
        Additional parameters passed to AlbersInfo constructor.

    Returns
    -------
    AlbersInfo
        Configured SHG grid info with lower_left_cell calculated.

    Examples
    --------
    >>> from pydsstools.core.gridinfo import build_shg_gridinfo, DataType
    >>> info = build_shg_gridinfo(
    ...     shape=(500, 700),
    ...     cell_size=2000.0,
    ...     min_xy=(-1500000, 500000),
    ...     data_type=DataType.inst_val,
    ...     data_units="M"
    ... )
    >>> print(info.lower_left_cell)
    (-750, 250)

    See Also
    --------
    AlbersInfo : Full Albers grid info class
    """
    # Merge with SHG defaults
    params = {**SHG_PARAMS}
    params.update({
        "grid_type": GridType.albers_time,
        "shape": shape,
        "cell_size": cell_size,
        "min_xy": min_xy,
        "data_type": data_type,
        "data_units": data_units,
    })
    params.update(kwargs)

    info = AlbersInfo(**params)

    # Calculate lower_left_cell from min_xy
    info.update_lower_left_cell_from_minxy()

    return info


def update_albers_from_crs(gridinfo: AlbersInfo, crs_wkt: str) -> None:
    """Update Albers projection parameters from CRS WKT string.

    Parses the WKT and extracts Albers projection parameters, updating
    the gridinfo object in-place.

    Parameters
    ----------
    gridinfo : AlbersInfo
        Albers grid info object to update.
    crs_wkt : str
        Well-Known Text representation of coordinate reference system.

    Raises
    ------
    ValueError
        If CRS is not an equal-area conic projection.

    Notes
    -----
    Modifies gridinfo in-place. Updates:
    - proj_datum
    - proj_units
    - lat_0, lat_1, lat_2, lon_0
    - x_0, y_0

    Examples
    --------
    >>> from pydsstools.core.gridinfo import AlbersInfo, update_albers_from_crs
    >>> info = AlbersInfo(...)
    >>> wkt = '''PROJCS["NAD83 / Conus Albers", ...]'''
    >>> update_albers_from_crs(info, wkt)
    """
    if not is_equal_area_conic(crs_wkt):
        raise ValueError(
            "The provided CRS WKT does not represent an equal-area conic projection. "
            "Cannot update Albers gridinfo."
        )

    params = albers_params_from_wkt(crs_wkt)

    gridinfo.proj_datum = params["datum"]
    gridinfo.proj_units = params["proj_units"]
    gridinfo.lat_0 = params["lat_origin"]
    gridinfo.lat_1 = params["first_parallel"]
    gridinfo.lat_2 = params["second_parallel"]
    gridinfo.lon_0 = params["central_meridian"]
    gridinfo.x_0 = params["false_easting"]
    gridinfo.y_0 = params["false_northing"]

    logging.info("Updated Albers gridinfo from CRS WKT")
