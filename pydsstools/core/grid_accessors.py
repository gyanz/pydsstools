import logging
logger = logging.getLogger(__name__)
import numpy as np
from ..core import UNDEFINED
from ._accessors import register_grid_accessor
from .raster_grid import RasterSpatialGrid,has_rasterio,has_gdal
from .gridinfo import is_hrap_grid,is_albers_grid,is_specified_grid,is_undefined_grid
from .crs import wkt_to_crs,is_equal_area_conic,is_hrap

if has_rasterio:
    import rasterio
    from rasterio.profiles import DefaultGTiffProfile

    if has_gdal:
        #from rasterio._io import InMemoryRaster
        pass

    logger.debug("Registering raster accessor for spatial grid.")
    @register_grid_accessor("raster")
    class RasterAccessor:
        """
        Raster interface for :class:`SpatialGridStruct` via the ``.raster`` accessor.

        This accessor builds an in-memory rasterio dataset from the parent
        :class:`SpatialGridStruct` and exposes it as a :class:`RasterSpatialGrid`
        instance. Use ``grid.raster.inst()`` to obtain a raster-like object with
        convenience methods for plotting, masking, resampling, reprojection and
        exporting the grid as a GeoTIFF.

        The accessor infers the grid CRS and nodata value from
        ``grid_struct.gridinfo`` and prepares a default rasterio profile that can
        be used to construct temporary in-memory datasets compatible with both
        rasterio and GDAL.

        Parameters
        ----------
        grid_struct : SpatialGridStruct
            Parent grid object providing the grid data, dimensions, transform,
            grid type, CRS information and nodata metadata.

        Private Attributes
        ----------
        _obj : SpatialGridStruct
            The parent grid object to which this accessor is attached.
        _gridinfo : GridInfo
            Metadata describing the grid type, CRS, nodata, and extra info.
        _grid_type : GridType
            Enumerated type describing the logical grid type (HRAP, Albers, etc.).
        _grid_crs : str or pyproj.CRS or None
            Inferred CRS for the grid, or ``None`` if no CRS is available.
        _grid_nodata : float or int or None
            Nodata value inferred from ``gridinfo`` or its ``extra_info`` dict.
        _ds : rasterio.io.DatasetReader or None
            Lazily created in-memory rasterio dataset backing the raster operations.

        Notes
        -----
        - Nodata is taken from ``gridinfo.nodata`` if available, otherwise from
        ``gridinfo.extra_info['nodata']`` when present. If neither is defined,
        it defaults to ``UNDEFINED``.
        - The CRS used in the rasterio profile is, in order of precedence:
        an explicit override set on the parent object (``grid_struct._crs``),
        otherwise the CRS inferred from ``gridinfo``.
        - Use :meth:`override_crs` to safely override the CRS for compatible
        grid types (e.g., HRAP, Albers, specified grids).
        """
        def __init__(self, grid_struct):
            self._obj = grid_struct
            self._gridinfo = grid_struct.gridinfo
            self._grid_type = self._gridinfo.grid_type
            self._grid_crs = self._gridinfo._infer_crs()
            if not self._grid_crs.strip():
                self._grid_crs = None
            nodata = UNDEFINED # use UNDEFINED or np.nan or None instead?
            extra_info = self._gridinfo.extra_info
            try:
                nodata = self._gridinfo.nodata
            except Exception:
                if "nodata" in extra_info:
                    nodata = extra_info["nodata"]

            self._grid_nodata = nodata
            self._ds = None
        
        def _data(self,masked=False):
            buf = self._obj.read()
            if masked:
                return buf
            data = buf._data
            return data

        def _default_rasterio_profile(self):
            profile = DefaultGTiffProfile(count=1)
            # prepare rasterio profile
            row = self._obj.height
            col = self._obj.width
            if row < 256 or col < 256:
                profile.pop("blockxsize")
                profile.pop("blockysize")
            profile["transform"] = self._obj.transform  # gridinfo['grid_transform']
            # TODO: select float32 and float64 based on grid dtype
            profile["dtype"] = "float32"
            profile["nodata"] = self._grid_nodata
            profile["height"] = row
            profile["width"] = col
            # crs preference
            # 1. User defined
            # 2. grid_crs
            if self._obj._crs:
                logger.debug("Using CRS defined externally for the grid raster")
                profile["crs"] = self._obj._crs
            else:
                profile["crs"] = self._grid_crs
            return profile

        '''
        def _as_rasterio_datasource(self):
            # create in-memory rasterio datasource compatible with gdal
            if not has_gdal:
                raise Exception("Missing gdal library.")
            prof = self._default_rasterio_profile()
            ds = InMemoryRaster(
                self._data(), transform=prof["transform"], crs=prof["crs"]
            )
            return ds
        '''

        def _as_rasterio_dataset(self):
            # create in-memory rasterio dataset
            prof = self._default_rasterio_profile()
            memfile = rasterio.MemoryFile()
            data = self._data()
            # if UNDEFINED value is present but nodata is another value such as zero
            # change UNDEFINED to nodata
            # TODO: check if this can be implemented in the HEC-DSS C library
            if prof["nodata"] != UNDEFINED:
                logger.info("Setting UNDEFINED value to nodata in the raster.")
                data = np.where(data == UNDEFINED,prof["nodata"],data) 
            with memfile.open(**prof) as ds:
                ds.write(data, 1)
            ds = memfile.open()
            return ds

        def inst(self):
            """
            Instantiate and return a :class:`RasterSpatialGrid` for this grid.

            The first call creates an in-memory rasterio dataset from the
            parent :class:`SpatialGridStruct` using the default rasterio
            profile and caches it on the accessor. Subsequent calls reuse
            the same in-memory dataset.

            Returns
            -------
            RasterSpatialGrid
                Raster wrapper around the in-memory rasterio dataset, with
                convenience methods for plotting, masking, resampling,
                reprojection and exporting.
            """

            if self._ds is None:
                self._ds = self._as_rasterio_dataset()
            
            ds = RasterSpatialGrid(self._ds,**self._obj._profile3)
            return ds

        def override_crs(self,crs):
            """
            Override the CRS used for raster operations, with grid-type checks.

            The provided CRS is only accepted if it is compatible with the
            underlying grid type:

            - HRAP grids: CRS must look like an HRAP CRS (``is_hrap(crs)``).
            - Albers grids: CRS must be equal-area conic (``is_equal_area_conic``).
            - Specified grids: any CRS is accepted.
            - Undefined grids: any CRS is accepted.

            If the CRS is incompatible, the override is ignored and the
            parent object's ``_crs`` attribute is cleared.

            Parameters
            ----------
            crs : Any
                CRS object or input accepted by ``pyproj.CRS.from_user_input``,
                such as WKT, PROJ string, EPSG code, etc.
            """        

            if is_hrap_grid(self._grid_type) and is_hrap(crs):
                self._obj._crs = crs
            elif is_albers_grid(self._grid_type) and is_equal_area_conic(crs):
                self._obj._crs = crs
            elif is_specified_grid(self._grid_type):
                self._obj._crs = crs
            elif is_undefined_grid(self._grid_type):
                self._obj._crs = crs
            else:
                self._obj._crs=""
                logger.warning(f"CRS override provided for grid_type = {self._grid_type} is ignored due to incompatibility.")
