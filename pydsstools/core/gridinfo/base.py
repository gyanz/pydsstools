"""Base classes and common utilities for grid metadata.

This module provides the abstract base class and shared functionality for all
grid metadata types. It also includes type-checking utilities.
"""

import logging
from typing import Any, Tuple, List, Union, Optional, Iterable

try:
    from typing import Annotated, TypeAlias, Literal
except ImportError:
    from typing_extensions import Annotated, TypeAlias, Literal

from pydantic import (
    Field,
    AliasChoices,
    BaseModel,
    ConfigDict,
    PrivateAttr,
    model_validator,
)

from ..enums import GridType, DataType, CompressionMethod
from ..crs import (
    hrap,
    albers,
    albers_params_from_wkt,
    is_equal_area_conic,
    make_albers,
    crs_short_name,
)
from .._transform import Affine

__all__ = [
    "PairLikeInt",
    "PairLikeFloat",
    "GridTypeField",
    "is_undefined_grid",
    "is_hrap_grid",
    "is_albers_grid",
    "is_specified_grid",
    "GridInfoBase",
]

# ============================================================================
# Type Aliases
# ============================================================================

PairLikeInt: TypeAlias = Union[
    Tuple[int, int], Annotated[List[int], Field(min_length=2, max_length=2)]
]

PairLikeFloat: TypeAlias = Union[
    Tuple[float, float], Annotated[List[float], Field(min_length=2, max_length=2)]
]

#GridTypeField = Field(
#    validation_alias=AliasChoices("grid_type", "type", "gtype", "gridtype", "grid"),
#)
GridTypeField = Literal[
    GridType.undefined_time,GridType.undefined,
    GridType.hrap_time,GridType.hrap,
    GridType.albers_time,GridType.albers,
    GridType.specified_time,GridType.specified,
]


# ============================================================================
# Grid Type Checking Utilities
# ============================================================================

def is_undefined_grid(grid_type: GridType) -> bool:
    """Check if grid type is undefined.

    Attributes
    ----------
    grid_type : GridType
        The grid type enumeration value.

    Returns
    -------
    bool
        True if grid type is undefined or undefined_time.

    Examples
    --------
    >>> is_undefined_grid(GridType.undefined)
    True
    >>> is_undefined_grid(GridType.hrap)
    False
    """
    return grid_type in (GridType.undefined, GridType.undefined_time)


def is_hrap_grid(grid_type: GridType) -> bool:
    """Check if grid type is HRAP (Hydrologic Rainfall Analysis Project).

    HRAP uses a polar stereographic projection centered on the North Pole.

    Parameters
    ----------
    grid_type : GridType
        The grid type enumeration value.

    Returns
    -------
    bool
        True if grid type is hrap or hrap_time.

    Examples
    --------
    >>> is_hrap_grid(GridType.hrap_time)
    True
    >>> is_hrap_grid(GridType.albers)
    False
    """
    return grid_type in (GridType.hrap, GridType.hrap_time)


def is_albers_grid(grid_type: GridType) -> bool:
    """Check if grid type is Albers Equal Area Conic projection.

    Commonly used for Standard Hydrologic Grid (SHG) in HEC-HMS.

    Parameters
    ----------
    grid_type : GridType
        The grid type enumeration value.

    Returns
    -------
    bool
        True if grid type is albers or albers_time.

    Examples
    --------
    >>> is_albers_grid(GridType.albers_time)
    True
    >>> is_albers_grid(GridType.specified)
    False
    """
    return grid_type in (GridType.albers, GridType.albers_time)


def is_specified_grid(grid_type: GridType) -> bool:
    """Check if grid type uses user-specified projection.

    Specified grids use custom CRS definitions (WKT, PROJ, EPSG codes).

    Parameters
    ----------
    grid_type : GridType
        The grid type enumeration value.

    Returns
    -------
    bool
        True if grid type is specified or specified_time.

    Examples
    --------
    >>> is_specified_grid(GridType.specified_time)
    True
    >>> is_specified_grid(GridType.hrap)
    False
    """
    return grid_type in (GridType.specified, GridType.specified_time)


# ============================================================================
# Base Grid Info Class
# ============================================================================

class GridInfoBase(BaseModel):
    """Abstract base class for all DSS Version 7 grid metadata structures.

    This base class provides common functionality shared across all grid types:
    - Dynamic extra field handling
    - Coordinate system inference
    - Grid validation
    - DSS v6 compatibility

    All concrete grid info classes (GridInfo, HrapInfo, AlbersInfo, SpecifiedInfo)
    inherit from this base.

    Attributes
    ----------
    extra : dict[str, Any]
        Dictionary storing any additional fields not defined in the schema.
        Allows for extensibility without breaking validation.

    Notes
    -----
    This is an abstract base class. Use one of the concrete subclasses:
    - GridInfo (undefined grids)
    - HrapInfo (HRAP projection)
    - AlbersInfo (Albers projection)
    - SpecifiedInfo (user-defined projection)

    Or use the GridInfoCreate factory function which automatically selects
    the appropriate subclass based on grid_type.
    """

    model_config = ConfigDict(extra="allow", validate_default=True)

    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Storage for additional fields not in the schema"
    )

    @model_validator(mode="before")
    @classmethod
    def _bucket_extras(cls, data: Any) -> Any:
        """Collect unknown fields into the 'extra' dictionary.

        This validator runs before field validation and separates known
        fields from unknown ones, storing unknown fields in 'extra'.

        Parameters
        ----------
        data : Any
            Input data (typically dict) to validate.

        Returns
        -------
        dict
            Normalized data with unknown fields moved to 'extra'.
        """
        if not isinstance(data, dict):
            return data

        # Get declared field names
        declared = set(
            getattr(cls, "model_fields", {}) or getattr(cls, "__annotations__", {})
        )

        # Separate known vs unknown
        provided_extra = data.get("extra")
        extras = {k: v for k, v in data.items() if k not in declared and k != "extra"}
        known = {k: v for k, v in data.items() if k in declared}

        # Merge extras (user-supplied extras take precedence)
        merged_extra: dict[str, Any] = {}
        if isinstance(provided_extra, dict):
            merged_extra.update(provided_extra)
        merged_extra.update(extras)

        if merged_extra:
            known["extra"] = merged_extra
        return known

    def __setattr__(self, name: str, value: Any) -> None:
        """Override attribute setting to route unknown fields to 'extra'.

        Parameters
        ----------
        name : str
            Attribute name to set.
        value : Any
            Value to assign to the attribute.
        """
        declared = getattr(self.__class__, "model_fields", {}) or getattr(
            self.__class__, "__annotations__", {}
        )
        if name in declared or name == "extra" or name.startswith("_"):
            return super().__setattr__(name, value)
        # Unknown attributes go into .extra
        self.extra[name] = value

    def __repr_args__(self) -> Iterable[Tuple[str, Any]]:
        """Generate arguments for string representation.

        Only shows declared fields, not the 'extra' dictionary.

        Yields
        ------
        tuple[str, Any]
            Field name and value pairs for declared fields.
        """
        for name in self.__pydantic_fields__:
            if name != "extra" and name in self.__dict__:
                yield name, getattr(self, name)
        if "extra" in self.__dict__:
            yield "extra", self.extra

    @property
    def extra_info(self) -> dict[str, Any]:
        """Get dictionary of extra fields not in the schema.

        Returns
        -------
        dict[str, Any]
            Dictionary containing all extra/unknown fields.
        """
        return self.extra

    @property
    def all_info(self) -> dict[str, Any]:
        """Get complete dictionary of all fields including extras.

        Returns
        -------
        dict[str, Any]
            Complete dictionary representation using Pydantic's model_dump.
        """
        return self.model_dump()

    def get_v6_grid_type(self) -> GridType:
        """Get equivalent DSS Version 6 grid type.

        Converts DSS v7 grid types to their v6 equivalents. All v6 grids
        include time information (time-varying grids).

        Returns
        -------
        GridType
            The equivalent DSS v6 grid type (always the ``*_time`` variant).
        """
        if self.grid_type in [GridType.hrap, GridType.hrap_time]:
            return GridType.hrap_time
        elif self.grid_type in [GridType.albers, GridType.albers_time]:
            return GridType.albers_time
        elif self.grid_type in [GridType.specified, GridType.specified_time]:
            return GridType.specified_time
        else:
            return GridType.undefined_time

    def has_time(self) -> bool:
        """Check if grid type includes time information.

        Returns
        -------
        bool
            True if grid type is a ``*_time`` variant.
        """
        return self.grid_type in [
            GridType.undefined_time,
            GridType.hrap_time,
            GridType.albers_time,
            GridType.specified_time,
        ]

    def _infer_crs(self) -> str:
        """Infer coordinate reference system from grid metadata.

        This is a base implementation that checks the extra dict.
        Subclasses override this method to provide type-specific CRS inference.

        Returns
        -------
        str
            CRS definition string (WKT, PROJ, or EPSG code).
        """
        if "crs" in self.extra_info:
            return self.extra_info["crs"].strip()
        return ""

    def _infer_crs_name(self) -> str:
        """Infer short CRS name from grid metadata.

        This is a base implementation that checks the extra dict.
        Subclasses override this method to provide type-specific CRS name inference.

        Returns
        -------
        str
            Short CRS name or identifier.
        """
        if "crs_name" in self.extra_info:
            return self.extra_info["crs_name"].strip()
        return ""

    def normalize(self, transform: Affine = None):
        """Normalize coords_cell0 and/or lower_left_cell based on grid_type.

        This is implemented in the concrete classes.

        Parameters
        ----------
        transform : Affine or None, optional
            Affine transform of grid or raster data. Default is None.
        """
        pass
