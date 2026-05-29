"""HRAP grid type implementation and utilities.

This module provides the HrapInfo class and HRAP-specific utility functions.
HRAP (Hydrologic Rainfall Analysis Project) uses a polar stereographic
projection commonly used for precipitation data.
"""

import logging
logger = logging.getLogger(__name__)
from typing import Optional

try:
    from typing import Annotated, Literal
except ImportError:
    from typing_extensions import Annotated, Literal

from pydantic import Field, AliasChoices

from ..enums import GridType
from ..crs import hrap as hrap_crs
from .undefined import GridInfo
from .base import GridTypeField

__all__ = ["HrapInfo", "HRAP_CELL_SIZE"]


# HRAP standard cell size at 60°N latitude (meters)
HRAP_CELL_SIZE = 4762.5


class HrapInfo(GridInfo):
    """Metadata for HRAP (Hydrologic Rainfall Analysis Project) grid.

    HRAP uses a polar stereographic projection centered on the North Pole,
    commonly used for precipitation data in hydrologic modeling. The standard
    HRAP grid has 4.7625 km cell size at 60°N latitude.

    In addition to the parameters inherited from :class:`GridInfo`, this class
    adds ``data_source`` for tracking data provenance.

    Examples
    --------
    Create HRAP grid for NEXRAD precipitation:

    >>> from pydsstools.core.gridinfo import HrapInfo, GridType, DataType
    >>> info = HrapInfo(
    ...     grid_type=GridType.hrap,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=HRAP_CELL_SIZE,  # 4762.5 m
    ...     data_units="MM",
    ...     data_source="NEXRAD"
    ... )

    Or use the factory function (recommended):

    >>> from pydsstools.core.gridinfo import GridInfoCreate
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.hrap,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=HRAP_CELL_SIZE,
    ...     data_units="MM",
    ...     data_source="NEXRAD"
    ... )

    Notes
    -----
    **HRAP Projection Parameters:**

    * Projection: Polar Stereographic
    * Latitude of true scale: 60N
    * Central meridian: 105W
    * False easting: 401 grid cells
    * False northing: 1601 grid cells
    * Standard cell size: 4.7625 km at 60N

    **Typical Users:**

    * National Weather Service (NWS)
    * River Forecast Centers (RFCs)
    * HEC-HMS for precipitation input

    **Coordinate System:**

    * Origin is at the North Pole
    * X-axis points along 105W meridian
    * Grid cells are 4.7625 km x 4.7625 km at 60N
    * Standard grid covers the United States

    **Common Data Sources:**

    * NEXRAD - Next-Generation Radar
    * MPE - Multi-sensor Precipitation Estimator
    * RFC - River Forecast Center
    * PRISM - Parameter-elevation Regressions on Independent Slopes Model

    References
    ----------
    .. [hrap1] NOAA National Weather Service, "HRAP Coordinate System"
               https://www.nws.noaa.gov/oh/hrl/nwsrfs/users_manual/part2/_pdf/22hrap.pdf
    """

    grid_type: Annotated[
        Literal[GridType.hrap_time, GridType.hrap],
        Field(description="Grid type for HRAP grid data. Only hrap and hrap_time are valid.")
        ] = GridType.hrap_time
    """GridType: Type of grid projection. Only ``hrap`` and ``hrap_time`` are valid. Default ``GridType.hrap_time``."""

    data_source: str = Field(
        default="",
        validation_alias=AliasChoices(
            "data_source",
            "data_sources",
            "datasource",
            "datasources",
            "dsource",
            "dsources",
        ),
        description="Data source or provenance information"
    )
    """str: Source or provenance of the data. Common values: ``"NEXRAD"``, ``"MPE"``, ``"RFC"``, ``"PRISM"``. Default ``""``."""

    def _infer_crs(self) -> str:
        """Infer CRS for HRAP grid.

        Returns
        -------
        str
            HRAP CRS definition (PROJ or WKT format).
        """
        # Check if user provided custom CRS in extra
        if "crs" in self.extra_info:
            crs = self.extra_info["crs"].strip()
            if crs:
                logger.warning(
                    "Custom CRS found in extra_info for HRAP grid. "
                    "Using standard HRAP CRS instead."
                )

        return hrap_crs()

    def _infer_crs_name(self) -> str:
        """Infer CRS name for HRAP grid.

        Returns
        -------
        str
            Always returns "HRAP".
        """
        return "HRAP"
