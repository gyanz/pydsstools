import numpy as np
import numpy.ma as ma
from collections import namedtuple
from .._lib import SpatialGridStruct as SpatialGridStructBase
from .transform import TransformMethodsMixin, array_bounds, Affine
from .gridinfo import GridInfoCreate, DataType
from .gridv6_internals import gridinfo7_to_gridinfo6

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
    def profile(self):
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
                ("is_interval", True if self.is_interval else False),
                ("time_stamped", True if self.time_stamped else False),
                ("min_xy", self.get_min_xy()),
            ]
        )
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
                ("is_interval", True if self.is_interval else False),
                ("time_stamped", True if self.time_stamped else False),
                ("min_xy", self.get_min_xy()),
                ("gridinfo_version", self.version()),
                ("struct_version", self._struct_version()),
                ("struct_type", self._struct_type()),
            ]
        )

        val = prof["data_type"]
        prof["data_type"] = DataType[val.lower().replace("-", "_")]
        return GridInfoCreate(**prof)

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
                ("is_interval", True if self.is_interval else False),
                ("time_stamped", True if self.time_stamped else False),
            ]
        )

        val = prof["data_type"]
        prof["data_type"] = DataType[val.lower().replace("-", "_")]
        return prof

    @property
    def gridinfo_v6(self):
        info7 = self.gridinfo
        info6 = gridinfo7_to_gridinfo6(info7, self.pathname)
        return info6


class _SpatialGridStruct(SpatialGridStruct):
    """Private class that acts like SpatialGridStuct used to wrap raster dataset"""

    def __init__(self, data, grid_info):
        self._gridinfo = {key: val for key, val in grid_info.items()}
        self._data = {}
        if isinstance(data, ma.core.MaskedArray):
            self._data["data"] = data
        elif isinstance(data, np.ndarray):
            self._data["data"] = ma.masked_values(data, np.nan)
        else:
            raise Exception("Invalid data. It must be ndarray or masked array")
        print(data.shape)
        rows, cols = data.shape
        self._data["width"] = cols
        self._data["height"] = rows
        self._crs = self._gridinfo["crs"]

    def cellsize(self):
        return self.transform.xoff

    def origin_coords(self):
        xmin, xmax, ymin, ymax = self.get_extents()
        return (xmin, ymin)

    def lower_left_x(self):
        extent = self.get_extents()
        return extent[0]

    def lower_left_y(self):
        extent = self.get_extents()
        return extent[2]

    def get_extents(self):
        trans = self.transform
        width = self.width
        height = self.height
        xmin, ymin, xmax, ymax = array_bounds(height, width, trans)
        return (xmin, xmax, ymin, ymax)

    def _get_mview(self, dtype="f"):
        data = np.flipud(self._data["data"]._data.copy())
        return data

    def read(self):
        return self._data.get("data", None)

    @property
    def width(self):
        return self._data.get("width", None)

    @property
    def height(self):
        return self._data.get("height", None)

    @property
    def transform(self):
        return self._gridinfo.get("transform", None)

    def stats(self):
        # delegate stats computation to put_grid method
        # while saving to dss file
        # put_grid method will recompute stats if stats is empy or null equivalent value
        return {}

    @property
    def crs(self):
        return self._gridinfo.get("crs", None)

    @property
    def interval(self):
        return self.cellsize()

    @property
    def data_type(self):
        return self._gridinfo.get("data_type", None)

    @property
    def nodata(self):
        return self._data["data"].fill_value

    @property
    def units(self):
        return self._gridinfo.get("data_units", "")

    @property
    def profile(self):
        return self._gridinfo.copy()
