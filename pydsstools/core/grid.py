import logging
logger = logging.getLogger(__name__)
import numpy as np
import numpy.ma as ma
from collections import namedtuple
from .._lib import SpatialGridStruct as SpatialGridStructBase
from ._transform import TransformMethodsMixin, array_bounds, Affine
from .gridinfo import GridInfoCreate, is_albers_grid
from .enums import GridType, DataType
#from .gridv6_internals import gridinfo7_to_gridinfo6
from .gridinfo.v6.conversion import gridinfo7_to_gridinfo6
from .crs import albers_params_from_wkt, is_equal_area_conic

_BoundingBox = namedtuple("BoundingBox", ("left", "bottom", "right", "top"))


class BoundingBox(_BoundingBox):
    """Bounding box named tuple, defining extent in cartesian coordinates.
    .. code::
        BoundingBox(left, bottom, right, top)
    Attributes
    ----------
    left :
        Left coordinate
    bottom :
        Bottom coordinate
    right :
        Right coordinate
    top :
        Top coordinate
    """

    def _asdict(self):
        return {*zip(self._fields, self)}


class SpatialGridStruct(SpatialGridStructBase, TransformMethodsMixin):
    _accessors = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crs = ""  # private variable for use by raster accessor

    @property
    def width(self):
        return self.cols

    @property
    def height(self):
        return self.rows

    @property
    def transform(self):
        xmin, xmax, ymin, ymax = self.get_extents()
        cell = self.cell_size
        atrans = Affine(cell, 0, xmin, 0, -cell, ymax)
        return atrans

    @property
    def bounds(self):
        xmin, xmax, ymin, ymax = self.get_extents()
        return BoundingBox(xmin, ymin, xmax, ymax)

    @property
    def stats(self):
        result = {}
        result["max_val"] = self.max_val
        result["min_val"] = self.min_val
        result["mean_val"] = self.mean_val
        result["range_vals"] = self.range_vals
        result["range_counts"] = self.range_counts
        return result


    @property
    def gridinfo(self):
        prof = {}
        prof.update(
            [
                ("grid_type", self.grid_type2),
                ("data_units", self.data_units),
                ("data_type", self.data_type),
                ("lower_left_cell", self.lower_left_cell),
                ("shape", (self.rows, self.cols)),
                ("cell_size", self.cell_size),
                ("compression_method", self.compression_method2),
                ("compression_size", self.compression_size),
                ("compression_base", self.compression_base),
                ("compression_factor", self.compression_factor),
                ("max_val", self.max_val),
                ("min_val", self.min_val),
                ("mean_val", self.mean_val),
                ("range_vals", self.range_vals.tolist()),
                ("range_counts", self.range_counts.tolist()),
                ("nodata", self.nodata),
                ("crs", self.crs),
                ("crs_name", self.crs_name),
                ("data_source", self.data_source),
                ("coords_cell0", self.coords_cell0),
                ("tzid", self.tzid),
                ("tzoffset", self.tzoffset),
                ("is_interval", bool(self.is_interval)),
                ("time_stamped", bool(self.time_stamped)),
                ("min_xy", self.get_min_xy()),
                ("gridinfo_version", self.version()),
                ("struct_version", self._struct_version()),
                ("struct_type", self._struct_type()),
            ]
        )

        val = prof["data_type"]
        prof["data_type"] = DataType[val.lower().replace("-", "_")]
        if is_albers_grid(prof["grid_type"]):
            try:
                albers_params = albers_params_from_wkt(prof["crs"])
                prof.update(albers_params)
            except Exception:
                logger.debug("crs=\n%s",prof["crs"])
                logger.warning("Failed to extract Albers parameters from WKT")

        return GridInfoCreate(**prof)

    @property
    def gridinfo_v6(self):
        info7 = self.gridinfo
        info6 = gridinfo7_to_gridinfo6(info7, self.pathname)
        return info6

    @property
    def _profile1(self):
        result = {}
        result.update(
            [
                ("grid_type", self.grid_type),
                ("data_units", self.data_units),
                ("data_type", self.data_type),
                ("lower_left_cell", self.lower_left_cell),
                ("cols", self.cols),
                ("rows", self.rows),
                ("cell_size", self.cell_size),
                ("compression_method", self.compression_method),
                ("compression_size", self.compression_size),
                ("compression_base", self.compression_base),
                ("compression_factor", self.compression_factor),
                ("max_val", self.max_val),
                ("min_val", self.min_val),
                ("mean_val", self.mean_val),
                ("range_vals", self.range_vals.tolist()),
                ("range_counts", self.range_counts.tolist()),
                ("crs", self.crs),
                ("crs_name", self.crs_name),
                ("data_source", self.data_source),
                ("coords_cell0", self.coords_cell0),
                ("tzid", self.tzid),
                ("tzoffset", self.tzoffset),
                ("is_interval", bool(self.is_interval)),
                ("time_stamped", bool(self.time_stamped)),
                ("min_xy", self.get_min_xy()),
            ]
        )
        return result

    @property
    def _profile2(self):
        prof = {}
        prof.update(
            [
                ("grid_type", self.grid_type2),
                ("data_units", self.data_units),
                ("data_type", self.data_type),
                ("lower_left_cell", self.lower_left_cell),
                ("shape", (self.rows, self.cols)),
                ("cell_size", self.cell_size),
                ("compression_method", self.compression_method2),
                ("compression_size", self.compression_size),
                ("compression_base", self.compression_base),
                ("compression_factor", self.compression_factor),
                ("max_val", self.max_val),
                ("min_val", self.min_val),
                ("mean_val", self.mean_val),
                ("range_vals", self.range_vals.tolist()),
                ("range_counts", self.range_counts.tolist()),
                ("nodata", self.nodata),
                ("crs", self.crs),
                ("crs_name", self.crs_name),
                ("data_source", self.data_source),
                ("coords_cell0", self.coords_cell0),
                ("tzid", self.tzid),
                ("tzoffset", self.tzoffset),
                ("is_interval",  bool(self.is_interval)),
                ("time_stamped", bool(self.time_stamped)),
            ]
        )

        val = prof["data_type"]
        prof["data_type"] = DataType[val.lower().replace("-", "_")]
        return prof

    @property
    def _profile3(self):
        prof = {}
        prof.update(
            [
                ("grid_type", GridType(self.grid_type2)),
                ("data_units", self.data_units),
                ("data_type", self.data_type),
                ("lower_left_cell", self.lower_left_cell),
                ("cell_size", self.cell_size),
                ("max_val", self.max_val),
                ("min_val", self.min_val),
                ("mean_val", self.mean_val),
                ("range_vals", self.range_vals.tolist()),
                ("range_counts", self.range_counts.tolist()),
                ("data_source", self.data_source),
                ("coords_cell0", self.coords_cell0),
                ("tzid", self.tzid),
                ("tzoffset", self.tzoffset),
                ("is_interval",  bool(self.is_interval)),
                ("time_stamped", bool(self.time_stamped)),
            ]
        )

        val = prof["data_type"]
        prof["data_type"] = DataType[val.lower().replace("-", "_")]
        return prof
