"""Undefined grid type implementation.

This module provides the GridInfo class for basic/undefined grid types that
don't use specific projection information.
"""

from typing import Union, Tuple, List, Optional

try:
    from typing import Annotated, Literal
except ImportError:
    from typing_extensions import Annotated, Literal

from pydantic import Field, AliasChoices

from ..enums import GridType, DataType, CompressionMethod
from .base import GridInfoBase, PairLikeInt, PairLikeFloat, GridTypeField

__all__ = ["GridInfo"]


class GridInfo(GridInfoBase):
    """Metadata for undefined/basic grid type (DSS v7).

    This class represents grid data without specific projection information.
    It contains all basic grid properties: dimensions, cell size, compression,
    statistics, and optional spatial bounds.

    Use this grid type when working with generic raster data, when projection
    information is not available or not relevant, or when no coordinate
    transformation is needed.

    Examples
    --------
    Create a basic undefined grid:

    >>> from pydsstools.core.gridinfo import GridInfo, GridType, DataType
    >>> info = GridInfo(
    ...     grid_type=GridType.undefined,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=1000.0,
    ...     data_units="MM"
    ... )

    Or use the factory function (recommended):

    >>> from pydsstools.core.gridinfo import GridInfoCreate
    >>> info = GridInfoCreate(
    ...     grid_type=GridType.undefined,
    ...     data_type=DataType.per_aver,
    ...     shape=(100, 150),
    ...     cell_size=1000.0,
    ...     data_units="MM"
    ... )
    """

    grid_type: Annotated[
        Literal[GridType.undefined_time, GridType.undefined],
        Field(description="Grid type for undefined grid data. Only undefined and undefined_time are valid.")
    ] = GridType.undefined_time
    """GridType: Type of grid projection. Only ``undefined`` and ``undefined_time`` are valid. Default ``GridType.undefined_time``."""

    data_units: str = Field(
        default="",
        validation_alias=AliasChoices("data_units", "du", "data_unit"),
        description="Physical units of the grid data"
    )
    """str: Physical units of the data (e.g., "MM", "M", "CFS"). Default ``""``."""

    data_type: DataType = Field(
        validation_alias=AliasChoices("data_type", "dt", "datatype", "dtype"),
        description="Temporal data type (period average, instantaneous, etc.)"
    )
    """DataType: Temporal aggregation type (per_aver, per_cum, inst_val, inst_cum, freq). Required."""

    lower_left_cell: Optional[PairLikeInt] = Field(
        default=(0, 0),
        validation_alias=AliasChoices(
            "lower_left_cell",
            "llc",
            "llci",
            "lower_left_cell_index",
            "lower_cell",
            "ll_cell",
        ),
        description="Cell indices (x, y) of the lower-left grid cell"
    )
    """tuple[int, int] or None: (x, y) indices of the lower-left cell. Default ``(0, 0)``."""

    shape: Union[Tuple[int, int], Annotated[List[int], Field(min_length=2, max_length=2)]] = Field(
        description="Grid dimensions as (rows, columns)"
    )
    """tuple[int, int]: Grid dimensions as (rows, columns). Required."""

    cell_size: float = Field(
        validation_alias=AliasChoices(
            "cell_size", "cellsize", "cs", "dx", "spacing", "grid_size"
        ),
        description="Cell size in arbitrary units (assumes square cells)"
    )
    """float: Cell size in projection units (assumed square cells). Required."""

    compression_method: CompressionMethod = Field(
        default=CompressionMethod.zlib,
        validation_alias=AliasChoices("compression_method", "compression", "comp"),
        description="Compression algorithm for data storage"
    )
    """CompressionMethod: Compression algorithm for data storage. Default ``CompressionMethod.zlib``."""

    compression_base: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "compression_base", "comp_base", "compbase", "base", "compressionbase"
        ),
        description="Base offset for compression scaling"
    )
    """float: Base value for compression scaling. Default ``0.0``."""

    compression_factor: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "compression_factor",
            "comp_factor",
            "comp_scale",
            "compression_scale",
            "scale",
        ),
        description="Scale factor for compression"
    )
    """float: Scale factor for compression. Default ``0.0``."""

    max_val: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "max_val", "max", "maximum", "max_value", "mx", "maxima"
        ),
        description="Maximum value in grid data"
    )
    """float: Maximum data value in grid. Default ``0.0``."""

    min_val: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "min_val", "min", "minimum", "min_value", "minima"
        ),
        description="Minimum value in grid data"
    )
    """float: Minimum data value in grid. Default ``0.0``."""

    mean_val: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "mean_val", "mean", "mean_value", "average", "avg"
        ),
        description="Mean value of grid data"
    )
    """float: Mean data value in grid. Default ``0.0``."""

    range_vals: Annotated[List[float], Field(min_length=0)] = Field(
        default_factory=list,
        validation_alias=AliasChoices("range_vals", "rv", "range_values", "rangevals"),
        description="Histogram bin edges for data distribution"
    )
    """list[float]: Histogram bin edges for data distribution. Default ``[]``."""

    range_counts: Annotated[List[int], Field(min_length=0)] = Field(
        default_factory=list,
        validation_alias=AliasChoices("range_counts", "rc", "rangecounts"),
        description="Count of values in each histogram bin"
    )
    """list[int]: Count of values in each histogram bin. Default ``[]``."""

    min_xy: Optional[PairLikeFloat] = Field(
        default=None,
        validation_alias=AliasChoices("min_xy", "minxy", "xy_min", "xymin", "llxy"),
        description="Minimum (x, y) coordinates of grid extent (if known)"
    )
    """tuple[float, float] or None: (x_min, y_min) coordinates of grid extent. Default ``None``."""

