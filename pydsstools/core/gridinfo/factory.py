"""Factory function for creating grid metadata objects.

This module provides the GridInfoCreate factory function which automatically
selects and instantiates the appropriate grid info class based on grid_type.
"""

from typing import Union

try: # python 3.10+
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from pydantic import Field, TypeAdapter

from .undefined import GridInfo
from .hrap import HrapInfo
from .albers import AlbersInfo
from .specified import SpecifiedInfo
from .base import GridInfoBase

__all__ = ["GridInfoCreate", "GridInfoUnionType"]


# Type union for discriminated validation
GridInfoUnionType = Annotated[
    Union[GridInfo, HrapInfo, AlbersInfo, SpecifiedInfo],
    Field(discriminator="grid_type"),
]


def GridInfoCreate(**kwargs) -> GridInfoBase:
    """Factory function to create appropriate GridInfo subclass.

    Automatically selects the correct GridInfo subclass (GridInfo, HrapInfo,
    AlbersInfo, or SpecifiedInfo) based on the grid_type parameter.

    This is the recommended way to create grid metadata objects as it:

    - Provides type validation
    - Ensures correct class selection
    - Validates all required fields
    - Applies default values

    Parameters
    ----------
    **kwargs
        Keyword arguments for grid metadata. Must include 'grid_type'.
        Other required/optional parameters depend on the grid type.

    Returns
    -------
    GridInfoBase
        Instance of GridInfo, HrapInfo, AlbersInfo, or SpecifiedInfo.

    Raises
    ------
    TypeError
        If no keyword arguments provided.
    ValidationError
        If required fields are missing or invalid.

    Examples
    --------
    Create HRAP grid metadata:

    >>> from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.hrap,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=4762.5,
    ...     data_units="MM",
    ...     data_source="NEXRAD"
    ... )
    >>> type(info).__name__
    'HrapInfo'

    Create Albers/SHG grid metadata:

    >>> info = GridInfoCreate(
    ...     grid_type=GridType.albers,
    ...     data_type=DataType.inst_val,
    ...     shape=(500, 700),
    ...     cell_size=2000.0,
    ...     proj_datum=Datum.nad83,
    ...     lat_0=23.0,
    ...     lat_1=29.5,
    ...     lat_2=45.5,
    ...     lon_0=-96.0,
    ...     min_xy=(-1500000, 500000),
    ...     data_units="M"
    ... )
    >>> type(info).__name__
    'AlbersInfo'

    Create specified grid with custom CRS:

    >>> info = GridInfoCreate(
    ...     grid_type=GridType.specified,
    ...     data_type=DataType.per_aver,
    ...     shape=(200, 300),
    ...     cell_size=1000.0,
    ...     crs="EPSG:32610",
    ...     crs_name="WGS84 / UTM zone 10N",
    ...     nodata=-9999.0,
    ...     min_xy=(500000, 4000000),
    ...     data_units="MM"
    ... )
    >>> type(info).__name__
    'SpecifiedInfo'

    Create undefined/basic grid:

    >>> info = GridInfoCreate(
    ...     grid_type=GridType.undefined,
    ...     data_type=DataType.inst_val,
    ...     shape=(100, 100),
    ...     cell_size=1000.0,
    ...     data_units="M"
    ... )
    >>> type(info).__name__
    'GridInfo'

    With extra fields:

    >>> info = GridInfoCreate(
    ...     grid_type=GridType.hrap,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=4762.5,
    ...     data_units="MM",
    ...     custom_field="custom_value",  # Goes to extra dict
    ...     another_field=123
    ... )
    >>> info.extra_info['custom_field']
    'custom_value'

    Notes
    -----
    The factory uses Pydantic's discriminated union feature to automatically
    select the correct class based on grid_type. This provides:

    - Better error messages for invalid fields
    - Type-specific validation
    - Clear separation of grid type concerns

    Grid Type Mapping:

    - GridType.undefined or undefined_time → GridInfo
    - GridType.hrap or hrap_time → HrapInfo
    - GridType.albers or albers_time → AlbersInfo
    - GridType.specified or specified_time → SpecifiedInfo
    """
    if not kwargs:
        raise TypeError(
            "Provide keyword arguments to create GridInfo "
            "(e.g., grid_type=GridType.hrap, ...)"
        )

    # Use Pydantic TypeAdapter for discriminated validation
    adapter = TypeAdapter(GridInfoUnionType)
    return adapter.validate_python(kwargs)
