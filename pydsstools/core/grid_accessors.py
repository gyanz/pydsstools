import logging
import traceback
from contextlib import contextmanager
import numpy.ma as ma
# from .._lib import BoundingBox
from . import UNDEFINED
from .gridinfo import is_hrap_grid,is_albers_grid,is_specified_grid,is_undefined_grid
from .transform import Affine, from_bounds, from_origin, array_bounds
from .accessors import register_grid_accessor
from .grid import BoundingBox
from .gridinfo import GridType
from .crs import wkt_to_crs,is_equal_area_conic,is_hrap
from pyproj import CRS

try:
    import rasterio
    from rasterio.warp import reproject, Resampling, calculate_default_transform
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.crs import CRS
    from rasterio.plot import show as _show  # matplotlib?
    from rasterio import mask as riomask
    import numpy as np
    import json
except Exception:
    logging.debug("Missing rasterio library ...")
    logging.debug("Raster accessor for spatial grid not available.")
    traceback.print_exc()
else:
    logging.info("Registering raster accessor for SpatialGridStruct")
    try:
        from osgeo import gdal

        gdal.UseExceptions()
        from osgeo import ogr
    except Exception:
        gdal = None

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
                logging.debug("Using CRS defined externally for the grid raster")
                profile["crs"] = self._obj._crs
            else:
                profile["crs"] = self._grid_crs
            return profile

        def _as_rasterio_datasource(self):
            # create in-memory rasterio datasource compatible with gdal
            from rasterio._io import InMemoryRaster

            prof = self._default_rasterio_profile()
            ds = InMemoryRaster(
                self._data(), transform=prof["transform"], crs=prof["crs"]
            )
            return ds

        def _as_rasterio_dataset(self):
            # create in-memory rasterio dataset
            prof = self._default_rasterio_profile()
            memfile = rasterio.MemoryFile()
            data = self._data()
            # if UNDEFINED value is present but nodata is another value such as zero
            # change UNDEFINED to nodata
            # TODO: check if this can be implemented in the HEC-DSS C library
            if prof["nodata"] != UNDEFINED:
                logging.info("Setting UNDEFINED value to nodata in the raster.")
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
                logging.warning(f"CRS override provided for grid_type = {self._grid_type} is ignored due to incompatibility.")


    class VectorShape(object):
        def __init__(self, shell, holes=None):
            if not isinstance(shell, (list, tuple)):
                raise Exception("Argument must a list or tuple")
            self.coords = []
            self.coords.append(tuple(shell))
            if holes:
                self.coords.extend(tuple(holes))

        @property
        def __geo_interface__(self):
            return {"type": "Polygon", "coordinates": self.coords}

        @classmethod
        def from_bounds(cls, xmin, ymin, xmax, ymax):
            return cls(
                [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
            )

    def guard_vector_mask(feat):
        """Transform feat to polygon feature if does not have __geo_interface__ attribute"""
        attr = getattr(feat, "__geo_interface__", None)
        if not attr is None:
            return feat
        elif isinstance(feat, str):
            return shapefile_to_shapes(feat)
        elif isinstance(feat, ogr.Feature):
            # TODO: this is not working
            data = json.loads(feat.ExportToJson())
            result = {}
            result.update([("type", data["type"]), ("geometry", data["geometry"])])
            return result
        elif isinstance(feat, BoundingBox):
            return VectorShape.from_bounds(feat.left, feat.bottom, feat.right, feat.top)
        elif isinstance(feat, (list, tuple)):
            if len(feat) > 0:
                attr = getattr(feat[0], "__geo_interface__", None)
                if not attr is None:
                    # list of shapely like shapes
                    return feat
                elif isinstance(feat[0], (list, tuple)):
                    # list of coordinates for polygon
                    return VectorShape(*feat)
                else:
                    raise Exception("Invalid shape list provided")
            else:
                raise Exception("Empty shape list provided")
        else:
            raise Exception("Invalid shape data")

    def shapefile_to_shapes(shape_file):
        from osgeo import ogr

        ds = ogr.Open(shape_file)
        lyr = ds.GetLayer(0)
        shapes = []
        for feat in lyr:
            shape = guard_vector_mask(feat)
            shapes.append(shape)
        return shapes
    

    class RasterSpatialGrid:
        """
        Lightweight raster wrapper around an in-memory rasterio dataset.

        This class provides a raster-like interface on top of a rasterio
        dataset, exposing common properties (transform, bounds, cell size,
        CRS, nodata) and methods for:

        - Reading data as a NumPy or masked array.
        - Plotting with matplotlib.
        - Resampling within the same CRS.
        - Reprojecting to a new CRS.
        - Masking with vector geometries (via ``rasterio.mask``).
        - Exporting the grid to a GeoTIFF.
        - Generating contour shapefiles using GDAL.

        Instances are usually created via :meth:`RasterAccessor.inst` and are
        intended to behave similarly to :class:`SpatialGridStruct`, but backed
        by a rasterio dataset instead of a DSS/structured grid.
        """
        def __init__(self, ds,**kwargs):
            self._ds = ds
            self._kwargs = kwargs
            # revise minimum x, y coordinates
            # self._ginfo.update_minxy_from_transform(self.transform)
            # revise lower left cell indices: compute (albers), set to 0,0 (specified)
            # self._ginfo.update_albers_lower_left_cell_from_minxy()
            # self._ginfo.update_specified_lower_left_cell()
            # revise coords of cell0: set to min_xy (specified grid)
            # self._ginfo.update_specified_coords_cell0_from_transform(self.transform) 

        def _make_rasterio_dataset(self,data,profile):
            """
            Create an in-memory rasterio dataset from data and a profile.

            Parameters
            ----------
            data : ndarray or None
                2D array of raster values to write into band 1. If ``None``,
                an empty writable dataset is created using the provided
                profile (no data are written).
            profile : dict
                Rasterio profile (``driver``, ``dtype``, ``width``, ``height``,
                ``transform``, ``crs``, etc.) used to initialize the dataset.

            Returns
            -------
            rasterio.io.DatasetReader or DatasetWriter
                In-memory rasterio dataset backed by ``MemoryFile``.
            """
            memfile = rasterio.MemoryFile()
            if data is None:
                # ds will be writable
                ds = memfile.open(**profile)
            else:
                # ds will be read only 
                with memfile.open(**profile) as ds:
                    ds.write(data, 1)
                ds = memfile.open()
            return ds

        def _make_gdal_datasource(self):
            # create in-memory gdal raster source
            if gdal is not None:
                prof = self.profile
                driver = gdal.GetDriverByName("MEM")
                # GDT_Float32 = 6
                # band = 1
                ds = driver.Create(
                    "", self.width, self.height, 1, 6
                )
                ds.SetProjection(self.crs)
                ds.SetGeoTransform(Affine.to_gdal(self.transform))
                srcband = ds.GetRasterBand(1)
                srcband.WriteArray(self.read())
                srcband.SetNoDataValue(self.nodata)
                return ds

        def read(self,masked=False):
            """
            Read raster data from band 1.

            Parameters
            ----------
            masked : bool, default False
                If True, return a :class:`numpy.ma.MaskedArray` where pixels
                equal to the band nodata value are masked. If False, return a
                plain :class:`numpy.ndarray`.

            Returns
            -------
            ndarray or numpy.ma.MaskedArray
                2D array of raster values for band 1.
            """

            return self._ds.read(1, masked=masked)

        def get_extents(self):
            """
            Compute bounding coordinates of the raster in map units.

            Returns
            -------
            tuple of float
                (xmin, xmax, ymin, ymax) in the dataset CRS.
            """
            trans = self.transform
            width = self.width
            height = self.height
            xmin, ymin, xmax, ymax = array_bounds(height, width, trans)
            return (xmin, xmax, ymin, ymax)

        def get_min_xy(self):
            """
            Return the minimum (x, y) coordinates of the raster bounds.

            Returns
            -------
            tuple of float
                (xmin, ymin) in the dataset CRS.
            """
            return self.bounds[0:2]

        @property
        def profile(self):
            return self._ds.meta

        @property
        def transform(self):
            return self.profile["transform"]

        @property
        def cell_size(self):
            return self.transform.a

        @property
        def bounds(self):
            xmin, xmax, ymin, ymax = self.get_extents()
            return BoundingBox(xmin, ymin, xmax, ymax)
        
        @property
        def rows(self):
            return self.profile["height"]

        @property
        def cols(self):
            return self.profile["width"]

        @property
        def width(self):
            return self.cols

        @property
        def height(self):
            return self.rows

        @property
        def crs(self,pyproj_crs=False):
            if pyproj_crs:
                return CRS(self.profile["crs"])

            return self.profile["crs"].to_wkt()

        @property
        def nodata(self):
            return self.profile["nodata"]

        @property
        def data_units(self):
            return self._kwargs.get("data_units","")

        @property
        def data_type(self):
            return self._kwargs.get("data_type","")
        
        @property
        def grid_type(self):
            grid_type = self._kwargs.get("grid_type",None)
            if grid_type:
                return grid_type
            else:
                crs = self.crs
                if not crs:
                    return GridType.undefined_time
                if is_hrap(crs):
                    return GridType.hrap_time
                elif is_equal_area_conic(crs):
                    return GridType.albers_time
                else:
                    return GridType.specified_time

        def gridinfo_dict(self):
            ginfo = {}
            ginfo["grid_type"] = self.grid_type
            ginfo["data_units"] = self.data_units
            ginfo["data_type"] = self.data_type
            ginfo["cols"] = self.cols
            ginfo["rows"] = self.rows
            ginfo["cell_size"] = self.cell_size
            ginfo["nodata"] = self.nodata
            ginfo["crs"] = self.crs
            return ginfo

        def plot(self, **kwargs):
            """
            Plot the raster using rasterio.plot.show with optional colorbar.

            Parameters
            ----------
            mask_zeros : bool, default False
                If True, cells equal to 0 are also treated as missing and
                plotted as transparent (NaN).
            colorbar : bool, default True
                If True, draw a colorbar using matplotlib. Ignored when an
                external ``ax`` is provided.
            cmap : str, default "Spectral"
                Matplotlib colormap name.

            Other Parameters
            ----------------
            **kwargs
                Additional keyword arguments are passed through to
                :func:`rasterio.plot.show`.

            Notes
            -----
            - The underlying data are read as a masked array; existing nodata
              pixels are converted to NaN for plotting.
            - When ``ax`` is supplied or ``colorbar`` is False, the function
              only draws the image and does not create a colorbar.
            """
            # treat zero as nodata
            mask_zeros = kwargs.pop("mask_zeros", False)  
            # flag for showing colorbar
            colorbar = kwargs.pop("colorbar", True)
            # matplotlib colormap
            cmap = kwargs.get("cmap", "Spectral")
            kwargs["cmap"] = cmap
            buf = self.read(masked=True)
            mask = buf.mask
            #TODO: is copy necessary?
            data = buf._data.copy()
            trans = self.transform
            data[mask] = np.nan
            if mask_zeros:
                data[data == 0] = np.nan
            if "ax" in kwargs or not colorbar:
                _show(data, transform=trans, **kwargs)
            else:
                import matplotlib.pyplot as plt

                fig, ax = plt.subplots()
                image = ax.imshow(data, cmap=cmap)  # hidden just for colorbar
                _show(data, transform=trans, ax=ax, **kwargs)
                fig.colorbar(image, ax=ax, label=self.data_units)
                plt.show()

        def save_tiff(self, filepath):
            """
            Save the raster to a GeoTIFF file.

            Parameters
            ----------
            filepath : str or path-like
                Path of the output GeoTIFF file. The current dataset profile
                (including CRS, transform, dtype, nodata) is preserved.
            """
            data = self.read()
            profile = self.profile
            with rasterio.open(filepath, "w", **profile) as dst:
                dst.write(data, 1)

        def resample(self, scale, method=Resampling.bilinear, memory=64):
            """
            Resample the raster by a uniform scale factor in x and y.

            Parameters
            ----------
            scale : float
                Scale factor for pixel size. Values > 1 coarsen the grid
                (larger pixels, fewer rows/cols); values < 1 refine it.
            method : rasterio.enums.Resampling, default Resampling.bilinear
                Resampling algorithm to use (nearest, bilinear, cubic, etc.).
            memory : int, default 64
                Approximate warp memory limit in megabytes passed to
                :func:`rasterio.warp.reproject`.

            Returns
            -------
            RasterSpatialGrid
                New :class:`RasterSpatialGrid` instance with resampled data.

            Raises
            ------
            NotImplementedError
                If called on HRAP or HRAP-time grids, where resampling is
                explicitly not implemented.
            """
            if self.grid_type in (GridType.hrap,GridType.hrap_time):
                raise NotImplementedError("Resampling not implemented for HRAP grid.")
            
            src_prof = self.profile
            src_trans = self.transform
            nodata = self.nodata
            crs = self.crs

            dst_trans = Affine(
                src_trans.a * scale,
                src_trans.b,
                src_trans.c,
                src_trans.d,
                src_trans.e * scale,
                src_trans.f,
            )

            dst_prof = dict(src_prof)
            dst_prof["transform"] = dst_trans
            dst_prof["width"] = int(src_prof["width"] // scale)
            dst_prof["height"] = int(src_prof["height"] // scale)
            dst_width = dst_prof["width"]
            dst_height = dst_prof["width"]

            src_data = self.read()
            dst_data = np.empty((dst_height, dst_width), np.float32)
            logging.info(
                "Resampling SRC transform = %r, Shape = %r,%r"
                % (src_trans, src_prof["height"], src_prof["width"])
            )
            logging.info(
                "Resampling DST transform = %r, Shape = %r,%r"
                % (dst_trans, dst_height, dst_width)
            )

            reproject(
                src_data,
                dst_data,
                src_nodata=nodata,
                dst_nodata=nodata,
                src_transform=src_trans,
                dst_transform=dst_trans,
                src_crs=crs,
                dst_crs=crs,
                resampling=method,
                warp_mem_limit=memory,
            )

            ds = self._make_rasterio_dataset(dst_data, dst_prof)
            obj = RasterSpatialGrid(ds,grid_type=self.grid_type,data_units=self.data_units,data_type=self.data_type)
            return obj

        def reproject(self, dst_crs, method=Resampling.nearest, cellsize=None):
            """
            Reproject the raster to a new CRS.

            Parameters
            ----------
            dst_crs : Any
                Target CRS, in any form accepted by rasterio (e.g., WKT,
                PROJ string, EPSG code, or dict).
            method : rasterio.enums.Resampling, default Resampling.nearest
                Resampling algorithm to use during reprojection.
            cellsize : float or tuple, optional
                Target pixel size (in units of ``dst_crs``). If None, a
                default resolution is chosen by
                :func:`rasterio.warp.calculate_default_transform`.

            Returns
            -------
            RasterSpatialGrid
                New :class:`RasterSpatialGrid` instance in the target CRS,
                with appropriately sized output grid and transform.
            """
            src_prof = self.profile
            src_trans = self.transform
            src_width = self.width
            src_height = self.height
            src_crs = self.crs
            src_data = self.read()

            dst_transform, dst_width, dst_height = calculate_default_transform(src_crs, dst_crs, src_width, src_height, *self.bounds, resolution=cellsize)
            dst_prof = src_prof.copy()
            dst_prof.update({
                "crs": dst_crs,
                "transform": dst_transform,
                "width": dst_width,
                "height": dst_height
            })
            dst_ds = self._make_rasterio_dataset(None,dst_prof)
            reproject(
                source=src_data,
                destination=rasterio.band(dst_ds, 1),
                src_transform=src_trans,
                src_crs=src_crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=method
            )
            obj = RasterSpatialGrid(dst_ds,data_units=self.data_units,data_type=self.data_type)
            return obj

        def mask(
            self,
            poly,
            all_touched=False,
            invert=False,
            filled=True,
            crop=False,
            pad=False,
            pad_width=0,
        ):
            """
            Mask the raster using vector geometries and return a new grid.

            This is a thin wrapper around :func:`rasterio.mask.mask` that
            accepts a variety of geometry inputs and returns a new
            :class:`RasterSpatialGrid` instance.

            Parameters
            ----------
            poly : str, list, tuple, object
                Shapefile path, any geometry implementing ``__geo_interface__``,
                list/tuple of such geometries, or a :class:`BoundingBox`.
            all_touched : bool, default False
                If True, all pixels touched by geometries will be included
                in the mask; otherwise only pixels whose center is within
                the polygon are used.
            invert : bool, default False
                If True, mask the pixels *inside* the shapes instead of
                outside.
            filled : bool, default True
                If True, return an ndarray with masked pixels set to the
                dataset nodata value. If False, return a masked array.
            crop : bool, default False
                If True, crop the output to the extent of the shapes.
            pad : bool, default False
                If True, pad the cropped extent by ``pad_width`` pixels.
            pad_width : int or float, default 0
                Number of pixels (or map units, depending on rasterio
                version) to pad the cropped extent.

            Returns
            -------
            RasterSpatialGrid
                New :class:`RasterSpatialGrid` with masked data and updated
                transform and dimensions.
            """
            shapes = guard_vector_mask(poly)
            if not isinstance(shapes, (list, tuple)):
                shapes = [shapes]
            logging.debug("Raster mask shapes = %r", shapes)

            src_prof = self.profile
            ds = self._ds
            dst_data, dst_transform = riomask.mask(
                ds,
                shapes,
                all_touched=all_touched,
                invert=invert,
                filled=filled,
                crop=crop,
                pad=pad,
                pad_width=pad_width,
            )
            dst_data = np.ma.masked_values(dst_data, self.nodata)
            dst_prof = src_prof.copy()
            dst_prof["transform"] = dst_transform

            dst_ds = self._make_rasterio_dataset(dst_data[0],dst_prof)
            obj = RasterSpatialGrid(dst_ds,grid_type=self.grid_type,data_units=self.data_units,data_type=self.data_type)
            return obj

        def generate_contours(self, shape_file, **kwargs):
            """
            Generate contour lines and save them as a shapefile using GDAL.

            Parameters
            ----------
            shape_file : str or path-like
                Path of the output contour shapefile.
            base : float, default 0
                Base elevation relative to which contour intervals are
                generated.
            interval : float, default 10
                Elevation interval between successive contour lines.
            fixed_levels : list of float, default []
                Additional specific elevations at which contours are
                generated, in addition to the regular interval.
            ignore_nodata : bool, default True
                If True, pixels equal to the nodata value are ignored during
                contour generation.

            Returns
            -------
            osgeo.ogr.DataSource or None
                OGR datasource for the created shapefile, or ``None`` if
                GDAL/OGR is not available.

            Notes
            -----
            - The output shapefile contains a ``MultiLineString`` layer with
              attributes ``ID`` (integer) and ``ELEV`` (real).
            - This method uses :func:`gdal.ContourGenerate` under the hood.
            """
            if gdal is not None:
                #  contour options
                interval = kwargs.get("interval", 10)
                base = kwargs.get("base", 0)
                fixed_levels = kwargs.get("fixed_levels", [])
                ignore_nodata = kwargs.get("ignore_nodata", True)
                use_nodata = 0 if ignore_nodata else 1

                # GDAL datasource
                ds1 = self._make_gdal_datasource()
                srcband = ds1.GetRasterBand(1)

                # create contour shape file
                crs = ogr.osr.SpatialReference()
                crs.ImportFromWkt(self.crs)
                ds2 = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shape_file)
                contour_layer = ds2.CreateLayer("contour", crs, ogr.wkbMultiLineString)
                field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
                contour_layer.CreateField(field_defn)
                field_defn = ogr.FieldDefn("ELEV", ogr.OFTReal)
                contour_layer.CreateField(field_defn)

                gdal.ContourGenerate(
                    srcband,
                    interval,
                    # interval, base
                    base,
                    # fixedlevelcount list
                    fixed_levels,
                    use_nodata,
                    self.nodata, 
                    contour_layer,
                    0,
                    1,
                )

                return ds2









