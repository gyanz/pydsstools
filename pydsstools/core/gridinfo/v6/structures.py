"""DSS Version 6 grid metadata ctypes structures.

This module contains the C-compatible structures used for DSS v6 grid I/O.
These structures are used for binary serialization and interaction with the
HEC-DSS C library.

Grid Type Codes
---------------
- 400/401: Undefined grid
- 410/411: HRAP grid
- 420/421: Albers grid
- 430/431: Specified grid

The even codes (400, 410, 420, 430) indicate time-varying grids.
The odd codes (401, 411, 421, 431) indicate static grids.

See Also
--------
conversion : Conversion functions between v6 and v7 formats
"""

import logging
import ctypes
import numpy as np
from typing import Optional

from ...crs import hrap, make_albers, crs_short_name
from ..factory import GridInfoCreate
from .conversion import ints_to_str, int32_to_float32, float32_to_int32
from .conversion import gridinfo6_to_gridinfo7_dict


__all__ = [
    "GRIDINFO_VERSION",
    "SPECIFIED_GRID_INFO_VERSION",
    "GridInfo6",
    "HrapInfo6",
    "AlbersInfo6",
    "SpecifiedInfo6",
]

# Grid info version constants
SPECIFIED_GRID_INFO_VERSION = 2  # Used by DSSVue for specified grids
GRIDINFO_VERSION = 1  # Used by DSSVue for other grid types


# ============================================================================
# Base DSS v6 Grid Info Class
# ============================================================================

class GridInfo6Base:
    """Base class for DSS Version 6 grid metadata structures.

    Provides common methods for all v6 grid types (GridInfo6, HrapInfo6,
    AlbersInfo6, SpecifiedInfo6). These methods handle:

    - Conversion between Python objects and int32 arrays (for C interface)
    - Serialization to/from dictionaries
    - CRS inference from grid parameters
    - Conversion to DSS v7 format

    This class uses ctypes.Structure for memory layout compatible with
    the HEC-DSS C library.
    """

    def version(self) -> int:
        """Get grid info version number.

        Returns
        -------
        int
            Version number (1 for most grids, 2 for specified grids).
        """
        if self.grid_type == 430:
            return SPECIFIED_GRID_INFO_VERSION

        return GRIDINFO_VERSION

    @classmethod
    def from_grid_type(cls, grid_type_info):
        """Factory method to create appropriate GridInfo6 subclass.

        Parameters
        ----------
        grid_type_info : str or int
            Grid type identifier. Can be:
            - String: "hrap", "albers", "specified", "undefined"
            - Integer code: 400, 410, 420, 430 (and variants)

        Returns
        -------
        GridInfo6 or subclass
            Instance of GridInfo6, HrapInfo6, AlbersInfo6, or SpecifiedInfo6.
        """
        if isinstance(grid_type_info, str):
            grid_type_info = grid_type_info.lower()

        if grid_type_info in ["hrap", "hrap-time", "hraptime", "410", "411", 410, 411]:
            info = HrapInfo6(grid_type=410)
            fsize = ctypes.sizeof(HrapInfo6)
            size = 128
            gsize = 124
        elif grid_type_info in [
            "alber",
            "albers",
            "albers-time",
            "alberstime",
            "alber-time",
            "420",
            "421",
            420,
            421,
        ]:
            info = AlbersInfo6(grid_type=420)
            fsize = ctypes.sizeof(AlbersInfo6)
            size = 164
            gsize = 124
        elif grid_type_info in [
            "specified",
            "spec",
            "specified-time",
            "specifiedtime",
            "430",
            "431",
            430,
            431,
        ]:
            info = SpecifiedInfo6(grid_type=430)
            fsize = ctypes.sizeof(SpecifiedInfo6)
            size = 160
            gsize = 124
        else:
            info = GridInfo6(grid_type=400)
            fsize = ctypes.sizeof(GridInfo6)
            size = 124
            gsize = 124

        info.info_fsize = fsize
        info.info_size = size
        info.info_gsize = gsize
        return info

    @classmethod
    def get_specinfo6(cls, crs_name_length=30, crs_def_length=150, tzid_length=30):
        """Create SpecifiedInfo6 with custom string field lengths.

        SpecifiedInfo6 has variable-length string fields (crs_name, crs_def,
        tzid). This method allocates arrays of specified sizes.

        Parameters
        ----------
        crs_name_length : int, optional
            Length of CRS name field in int32 units, default 30.
        crs_def_length : int, optional
            Length of CRS definition field in int32 units, default 150.
        tzid_length : int, optional
            Length of time zone ID field in int32 units, default 30.

        Returns
        -------
        SpecifiedInfo6
            Initialized SpecifiedInfo6 with allocated string arrays.
        """
        info = SpecifiedInfo6(grid_type=430)
        flat_size = ctypes.sizeof(SpecifiedInfo6)

        # Allocate crs_name
        count = crs_name_length
        flat_size += count * 4
        info.crs_name_length = count
        info.crs_name = (ctypes.c_int32 * count)(*[0 for x in range(count)])

        # Allocate crs_def
        count = crs_def_length
        flat_size += count * 4
        info.crs_def_length = count
        info.crs_def = (ctypes.c_int32 * count)(*[0 for x in range(count)])

        # Allocate tzid
        count = tzid_length
        flat_size += count * 4
        info.tzid_length = count
        info.tzid = (ctypes.c_int32 * count)(*[0 for x in range(count)])

        info.info_fsize = flat_size
        return info

    def update_from_int_array(self, ar):
        """Deserialize grid info from int32 array.

        Reads field values from a flat int32 array (typically from C library)
        and populates the ctypes structure fields.

        Parameters
        ----------
        ar : list[int]
            Flat array of int32 values representing serialized grid info.

        Notes
        -----
        The array layout depends on grid_type. Variable-length fields in
        SpecifiedInfo6 require special handling.

        This method modifies the object in-place.
        """

        grid_type = ar[1]
        if self.grid_type != grid_type:
            logging.error(
                f"Cannot update info6 object (grid_type={self.grid_type}) with int "
                f"array of different grid_type ({grid_type})"
            )
            return

        fields = self._fields_
        info = self

        # Define index mappings for each grid type
        if grid_type == 400:
            # Undefined grid
            index2 = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                     18, 19, 20, 21, 22, 23, 43, 53]

        elif grid_type == 410:
            # HRAP grid
            index2 = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                     18, 19, 20, 21, 22, 23, 43, 63, 66]

        elif grid_type == 420:
            # Albers grid
            index2 = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                     18, 19, 20, 21, 22, 23, 43, 63, 64, 67, 68, 69, 70, 71,
                     72, 73, 74, 75]

        elif grid_type == 430:
            # Specified grid - variable length strings
            index2 = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                     18, 19, 20, 21, 22, 23, 43, 63, 64, 65, 65, 66, 67, 67,
                     68, 69, 70, 71, 71, 72, 73]

            # Adjust indices for variable-length fields
            crs_name_len = ar[index2[24]]
            index2[26] = index2[26] + crs_name_len  # crs_type
            index2[27] = index2[27] + crs_name_len  # crs_def_length

            crs_def_len = ar[index2[27]]
            index2[28] = index2[28] + crs_name_len  # crs_def
            index2[29] = index2[29] + crs_name_len + crs_def_len  # xcoords_cell0
            index2[30] = index2[30] + crs_name_len + crs_def_len  # ycoords_cell0
            index2[31] = index2[31] + crs_name_len + crs_def_len  # nodata
            index2[32] = index2[32] + crs_name_len + crs_def_len  # tz_length

            tzid_len = ar[index2[32]]
            index2[33] = index2[33] + crs_name_len + crs_def_len  # tzid
            index2[34] = index2[34] + crs_name_len + crs_def_len + tzid_len  # tzoffset
            index2[35] = index2[35] + crs_name_len + crs_def_len + tzid_len  # is_interval
            index2[36] = index2[36] + crs_name_len + crs_def_len + tzid_len  # time_stamped
            index2 = index2 + [index2[-1] + 1]

        indices = list(zip(index2[0:-1], index2[1:]))

        def get_type(_typ):
            """Extract base type from ctypes Array or Pointer."""
            if issubclass(_typ, (ctypes.Array, ctypes._Pointer)):
                return _typ._type_
            else:
                return _typ

        # Populate fields from int array
        for (name, typ), (start, end) in zip(fields, indices):
            length = end - start
            if name.endswith("_length"):
                old_name = name

            if ctypes.sizeof(typ) <= 4:
                # Simple int/float field
                val = ar[start]
                _typ = get_type(typ)
                if issubclass(_typ, (ctypes.c_float,)):
                    val = int32_to_float32(val)
                setattr(info, name, val)

            elif ctypes.sizeof(typ) == 8:
                # Pointer/array type
                _typ = get_type(typ)
                vals = []
                for i in range(start, end):
                    val = ar[i]
                    if issubclass(_typ, (ctypes.c_float,)):
                        val = int32_to_float32(val)
                    vals.append(val)
                if isinstance(vals[0], float):
                    setattr(info, name, (ctypes.c_float * length)(*vals))
                else:
                    setattr(info, name, (ctypes.c_int32 * length)(*vals))
                setattr(info, old_name, length)

            else:
                # Fixed array type
                _typ = get_type(typ)
                ptr = getattr(info, name)
                if length > 3:
                    # Range vals/counts
                    end = start + info.range_length

                for i in range(start, end):
                    val = ar[i]
                    if issubclass(_typ, (ctypes.c_float,)):
                        val = int32_to_float32(val)
                    ptr[i - start] = val

    def to_int_array(self) -> np.ndarray:
        """Serialize grid info to int32 array.

        Converts all fields to a flat int32 array suitable for passing to
        the C library.

        Returns
        -------
        np.ndarray
            1D array of int32 values representing the structure.
        """

        ginfo = self
        ibuff = []
        cls = type(ginfo)
        fields = cls()._fields_
        length = 0

        for name, typ in fields:
            if name.endswith("_length"):
                length = getattr(ginfo, name)

            if ctypes.sizeof(typ) <= 4:
                # Simple int/float data
                val = getattr(ginfo, name)
                if isinstance(val, (float,)):
                    val = float32_to_int32(val)
                ibuff.append(val)

            elif ctypes.sizeof(typ) == 8:
                # Pointer/array type
                ptr = getattr(ginfo, name)
                for i in range(length):
                    val = ptr[i]
                    if isinstance(val, (float,)):
                        val = float32_to_int32(val)
                    ibuff.append(val)
            else:
                # Fixed array type
                count = int(ctypes.sizeof(typ) / 4)
                ptr = getattr(ginfo, name)
                for i in range(count):
                    val = ptr[i]
                    if isinstance(val, (float,)):
                        val = float32_to_int32(val)
                    ibuff.append(val)

        return np.array(ibuff, dtype=np.int32)

    def to_dict(self) -> dict:
        """Convert grid info to Python dictionary.

        Converts all fields to a dictionary with string values decoded
        from int32 arrays.

        Returns
        -------
        dict
            Dictionary with field names as keys and converted values.
        """

        ginfo = self
        info = {}
        cls = type(ginfo)
        fields = cls()._fields_
        length = 0

        for name, typ in fields:
            if name.endswith("_length"):
                length = getattr(ginfo, name)

            if ctypes.sizeof(typ) <= 4:
                # Simple int/float data
                val = getattr(ginfo, name)
                info[name] = val

            elif ctypes.sizeof(typ) == 8:
                # Pointer/array type
                ptr = getattr(ginfo, name)
                data = []
                for i in range(length):
                    val = ptr[i]
                    data.append(val)
                if not name.endswith(("_vals", "_counts")):
                    # Convert to string
                    data = ints_to_str(data)
                info[name] = data

            else:
                # Fixed array type
                count = int(ctypes.sizeof(typ) / 4)
                data = []
                ptr = getattr(ginfo, name)
                for i in range(count):
                    val = ptr[i]
                    data.append(val)
                if not name.endswith(("_vals", "_counts")):
                    # Convert to string
                    data = ints_to_str(data)
                info[name] = data

        return info

    def get_fields(self) -> list[str]:
        """Get list of field names.

        Returns
        -------
        list[str]
            List of all field names in the structure.
        """
        ginfo = self
        cls = type(ginfo)
        fields = cls()._fields_
        names = [name for name, typ in fields]
        return names

    def to_gridinfo7(self):
        """Convert to DSS v7 GridInfo.

        Returns
        -------
        GridInfo or subclass
            DSS v7 grid info object (GridInfo, HrapInfo, AlbersInfo, or
            SpecifiedInfo).
        """
        prof7 = gridinfo6_to_gridinfo7_dict(self)
        return GridInfoCreate(**prof7)

    def _infer_crs(self) -> str:
        """Infer coordinate reference system from grid parameters.

        Returns
        -------
        str
            CRS definition (WKT, PROJ, or EPSG code).
        """
        crs = ""
        if self.grid_type == 410:
            # HRAP
            crs = hrap()

        elif self.grid_type == 420:
            # Albers
            crs = make_albers(
                self.proj_datum,
                self.false_easting,
                self.false_northing,
                self.central_meridian,
                self.first_parallel,
                self.sec_parallel,
                self.lat_origin,
                self.proj_units
            )

        elif self.grid_type == 430:
            # Specified
            length = self.crs_def_length
            ptr = self.crs_def
            data = []
            for i in range(length):
                val = ptr[i]
                data.append(val)
            # Convert to string
            crs = ints_to_str(data)

        return crs

    def _infer_crs_name(self) -> str:
        """Infer short CRS name from grid parameters.

        Returns
        -------
        str
            Short CRS name (e.g., "HRAP", "EPSG:5070").
        """
        if self.grid_type == 410:
            return "HRAP"

        elif self.grid_type == 420:
            return "ALBERS"

        elif self.grid_type == 430:
            length = self.crs_name_length
            ptr = self.crs_name
            data = []
            for i in range(length):
                val = ptr[i]
                data.append(val)
            # Convert to string
            crs_name = ints_to_str(data).strip()
            if not crs_name:
                # Try to extract from crs_def
                crs_name = crs_short_name(self._infer_crs())
                if crs_name is None:
                    crs_name = ""
            return crs_name

        return ""


# ============================================================================
# DSS v6 Grid Info Structures (ctypes)
# ============================================================================

class GridInfo6(GridInfo6Base, ctypes.Structure):
    """DSS v6 undefined/basic grid structure (grid_type 400).

    C-compatible structure for basic grid metadata.
    """
    _fields_ = [
        ("info_fsize", ctypes.c_int32),
        ("grid_type", ctypes.c_int32),
        ("info_size", ctypes.c_int32),
        ("info_gsize", ctypes.c_int32),
        ("stime", ctypes.c_int32),
        ("etime", ctypes.c_int32),
        ("data_units", ctypes.c_int32 * 3),
        ("data_type", ctypes.c_int32),
        ("lower_left_x", ctypes.c_int32),
        ("lower_left_y", ctypes.c_int32),
        ("cols", ctypes.c_int32),
        ("rows", ctypes.c_int32),
        ("cell_size", ctypes.c_float),
        ("compression_method", ctypes.c_int32),
        ("compression_size", ctypes.c_int32),
        ("compression_factor", ctypes.c_float),
        ("compression_base", ctypes.c_float),
        ("max_val", ctypes.c_float),
        ("min_val", ctypes.c_float),
        ("mean_val", ctypes.c_float),
        ("range_length", ctypes.c_int32),
        ("range_vals", ctypes.c_float * 20),
        ("range_counts", ctypes.c_int32 * 20),
    ]


class HrapInfo6(GridInfo6Base, ctypes.Structure):
    """DSS v6 HRAP grid structure (grid_type 410).

    Extends GridInfo6 with HRAP-specific field for data source.
    """
    _fields_ = [
        ("info_fsize", ctypes.c_int32),
        ("grid_type", ctypes.c_int32),
        ("info_size", ctypes.c_int32),
        ("info_gsize", ctypes.c_int32),
        ("stime", ctypes.c_int32),
        ("etime", ctypes.c_int32),
        ("data_units", ctypes.c_int32 * 3),
        ("data_type", ctypes.c_int32),
        ("lower_left_x", ctypes.c_int32),
        ("lower_left_y", ctypes.c_int32),
        ("cols", ctypes.c_int32),
        ("rows", ctypes.c_int32),
        ("cell_size", ctypes.c_float),
        ("compression_method", ctypes.c_int32),
        ("compression_size", ctypes.c_int32),
        ("compression_factor", ctypes.c_float),
        ("compression_base", ctypes.c_float),
        ("max_val", ctypes.c_float),
        ("min_val", ctypes.c_float),
        ("mean_val", ctypes.c_float),
        ("range_length", ctypes.c_int32),
        ("range_vals", ctypes.c_float * 20),
        ("range_counts", ctypes.c_int32 * 20),
        ("data_source", ctypes.c_int32 * 3),
    ]


class AlbersInfo6(GridInfo6Base, ctypes.Structure):
    """DSS v6 Albers grid structure (grid_type 420).

    Extends GridInfo6 with Albers projection parameters.
    """
    _fields_ = [
        ("info_fsize", ctypes.c_int32),
        ("grid_type", ctypes.c_int32),
        ("info_size", ctypes.c_int32),
        ("info_gsize", ctypes.c_int32),
        ("stime", ctypes.c_int32),
        ("etime", ctypes.c_int32),
        ("data_units", ctypes.c_int32 * 3),
        ("data_type", ctypes.c_int32),
        ("lower_left_x", ctypes.c_int32),
        ("lower_left_y", ctypes.c_int32),
        ("cols", ctypes.c_int32),
        ("rows", ctypes.c_int32),
        ("cell_size", ctypes.c_float),
        ("compression_method", ctypes.c_int32),
        ("compression_size", ctypes.c_int32),
        ("compression_factor", ctypes.c_float),
        ("compression_base", ctypes.c_float),
        ("max_val", ctypes.c_float),
        ("min_val", ctypes.c_float),
        ("mean_val", ctypes.c_float),
        ("range_length", ctypes.c_int32),
        ("range_vals", ctypes.c_float * 20),
        ("range_counts", ctypes.c_int32 * 20),
        ("proj_datum", ctypes.c_int32),
        ("proj_units", ctypes.c_int32 * 3),
        ("first_parallel", ctypes.c_float),
        ("sec_parallel", ctypes.c_float),
        ("central_meridian", ctypes.c_float),
        ("lat_origin", ctypes.c_float),
        ("false_easting", ctypes.c_float),
        ("false_northing", ctypes.c_float),
        ("xcoord_cell0", ctypes.c_float),
        ("ycoord_cell0", ctypes.c_float),
    ]


class SpecifiedInfo6(GridInfo6Base, ctypes.Structure):
    """DSS v6 specified grid structure (grid_type 430).

    Extends GridInfo6 with user-defined projection and time zone info.
    Uses variable-length string fields (pointers to int32 arrays).
    """
    _fields_ = [
        ("info_fsize", ctypes.c_int32),
        ("grid_type", ctypes.c_int32),
        ("info_size", ctypes.c_int32),
        ("info_gsize", ctypes.c_int32),
        ("stime", ctypes.c_int32),
        ("etime", ctypes.c_int32),
        ("data_units", ctypes.c_int32 * 3),
        ("data_type", ctypes.c_int32),
        ("lower_left_x", ctypes.c_int32),
        ("lower_left_y", ctypes.c_int32),
        ("cols", ctypes.c_int32),
        ("rows", ctypes.c_int32),
        ("cell_size", ctypes.c_float),
        ("compression_method", ctypes.c_int32),
        ("compression_size", ctypes.c_int32),
        ("compression_factor", ctypes.c_float),
        ("compression_base", ctypes.c_float),
        ("max_val", ctypes.c_float),
        ("min_val", ctypes.c_float),
        ("mean_val", ctypes.c_float),
        ("range_length", ctypes.c_int32),
        ("range_vals", ctypes.c_float * 20),
        ("range_counts", ctypes.c_int32 * 20),
        ("version", ctypes.c_int32),
        ("crs_name_length", ctypes.c_int32),
        ("crs_name", ctypes.POINTER(ctypes.c_int32)),
        ("crs_type", ctypes.c_int32),
        ("crs_def_length", ctypes.c_int32),
        ("crs_def", ctypes.POINTER(ctypes.c_int32)),
        ("xcoord_cell0", ctypes.c_float),
        ("ycoord_cell0", ctypes.c_float),
        ("nodata", ctypes.c_float),
        ("tzid_length", ctypes.c_int32),
        ("tzid", ctypes.POINTER(ctypes.c_int32)),
        ("tzoffset", ctypes.c_int32),
        ("is_interval", ctypes.c_int32),
        ("time_stamped", ctypes.c_int32),
    ]
