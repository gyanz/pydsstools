import logging
import traceback
# from contextlib import contextmanager
import numpy.ma as ma
from . import UNDEFINED
from .gridinfo import is_hrap_grid,is_albers_grid,is_specified_grid,is_undefined_grid, GridInfoCreate
from ._transform import Affine, from_bounds, from_origin, array_bounds
from .grid import BoundingBox
from .enums import GridType, DataType
from .crs import wkt_to_crs,is_equal_area_conic,is_hrap

has_rasterio = True
has_gdal = True

try:
    import rasterio
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.warp import reproject, Resampling, calculate_default_transform
    from rasterio.crs import CRS
    from rasterio.plot import show as _show  # matplotlib?
    from rasterio import mask as riomask
    import numpy as np
    import json
except Exception:
    has_rasterio = False
    logging.debug("Missing rasterio library ...")
    traceback.print_exc()
else:
    try:
        from osgeo import gdal
        gdal.UseExceptions()
        from osgeo import ogr
    except Exception:
        has_gdal = False

__all__ = ["RasterSpatialGrid"]

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
    def __init__(self, ds, **kwargs):
        self._ds = ds
        self._kwargs = kwargs
        self._owns_ds = False
        # revise minimum x, y coordinates
        # self._ginfo.update_minxy_from_transform(self.transform)
        # revise lower left cell indices: compute (albers), set to 0,0 (specified)
        # self._ginfo.update_albers_lower_left_cell_from_minxy()
        # self._ginfo.update_specified_lower_left_cell()
        # revise coords of cell0: set to min_xy (specified grid)
        # self._ginfo.update_specified_coords_cell0_from_transform(self.transform)

    @classmethod
    def from_file(cls, path, **kwargs):
        """
        Open a raster file and return a :class:`RasterSpatialGrid` instance.

        The instance owns the underlying dataset and should be closed when
        no longer needed — either via :meth:`close` or as a context manager.

        Parameters
        ----------
        path : str or path-like
            Path to any raster format supported by rasterio (GeoTIFF,
            GRIB, HDF5, etc.).
        **kwargs
            Passed through to :meth:`__init__` (e.g. ``grid_type``,
            ``data_units``, ``data_type``).

        Returns
        -------
        RasterSpatialGrid
        """
        ds = rasterio.open(path)
        obj = cls(ds, **kwargs)
        obj._owns_ds = True
        return obj

    def close(self):
        """Close the underlying dataset if this instance owns it."""
        if self._owns_ds and not self._ds.closed:
            self._ds.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        self.close()

    def _make_rasterio_dataset(self, data, profile):
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
        """Create an in-memory GDAL raster datasource from the current data.

        Returns
        -------
        osgeo.gdal.Dataset or None
            In-memory GDAL dataset with Float32 data, or None if GDAL
            is not available.
        """
        if has_gdal is not None:
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

        return self._ds.read(1, masked=masked).astype(np.float32, copy=False)

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
        """dict: Rasterio dataset metadata profile.

        Includes driver, dtype, crs, transform, width, height, etc.
        dtype is always reported as ``float32``. When the underlying
        dataset has no nodata value set, ``UNDEFINED`` is used.
        """
        meta = self._ds.meta
        meta["dtype"] = "float32"
        if meta["nodata"] is None:
            meta["nodata"] = UNDEFINED
        return meta

    @property
    def transform(self):
        """Affine: Affine transformation matrix.

        Maps pixel coordinates to map coordinates in the dataset CRS.
        """
        return self.profile["transform"]

    @property
    def cell_size(self):
        """float: Cell size (pixel width) in map units.

        Extracted from the ``a`` component of the affine transform.
        """
        return self.transform.a

    @property
    def bounds(self):
        """BoundingBox: Bounding box in map coordinates.

        Returns (xmin, ymin, xmax, ymax) computed from the transform and grid dimensions.
        """
        xmin, xmax, ymin, ymax = self.get_extents()
        return BoundingBox(xmin, ymin, xmax, ymax)

    @property
    def rows(self):
        """int: Number of rows (height) in the raster.

        Equivalent to the ``height`` key in the dataset profile.
        """
        return self.profile["height"]

    @property
    def cols(self):
        """int: Number of columns (width) in the raster.

        Equivalent to the ``width`` key in the dataset profile.
        """
        return self.profile["width"]

    @property
    def width(self):
        """int: Raster width in pixels.

        Alias for :attr:`cols`.
        """
        return self.cols

    @property
    def height(self):
        """int: Raster height in pixels.

        Alias for :attr:`rows`.
        """
        return self.rows

    @property
    def crs(self):
        """str: Coordinate reference system as WKT string.

        Converted from the rasterio CRS object in the dataset profile.
        """
        return self.profile["crs"].to_wkt()

    @property
    def nodata(self):
        """float: NoData value for missing/invalid pixels.

        Read from the dataset profile.
        """
        return self.profile["nodata"]

    @property
    def data_units(self):
        """str: Physical units of the data (e.g., "MM", "M", "CFS").

        Provided at construction via keyword arguments.
        """
        return self._kwargs.get("data_units","")

    @property
    def data_type(self):
        """DataType: Temporal aggregation type (per_aver, inst_val, etc.).

        Provided at construction via keyword arguments.
        """
        data_type = self._kwargs.get("data_type","")
        if data_type and isinstance(data_type,str):
            data_type = data_type.lower().replace("-","_")
        return data_type
    
    @property
    def grid_type(self):
        """GridType: Grid type inferred from CRS or explicitly set.

        If grid_type was provided at construction, returns that value.
        Otherwise, infers from CRS: HRAP projection returns hrap_time,
        equal-area conic returns albers_time, other CRS returns specified_time,
        and missing CRS returns undefined_time.
        """
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

    @property
    def gridinfo(self):
        """GridInfoBase: Grid metadata object (GridInfo, HrapInfo, AlbersInfo, or SpecifiedInfo).

        Creates and returns the appropriate GridInfo subclass based on
        grid_type, with coordinates normalized from the raster transform.
        """
        prof = self.gridinfo_dict()
        prof["data_type"] = DataType[prof["data_type"]]
        trans = self.transform
        ginfo = GridInfoCreate(**prof)
        ginfo.normalize(trans)
        return ginfo

    def gridinfo_dict(self):
        """Build a dictionary of grid metadata for GridInfoCreate.

        Returns
        -------
        dict
            Dictionary containing grid_type, shape, data_units, data_type,
            cols, rows, cell_size, nodata, and crs.
        """
        ginfo = {}
        ginfo["grid_type"] = self.grid_type
        ginfo["shape"] = (self.rows,self.cols)
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

    def resample(self, scale, method=None, memory=64):
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
        
        if method is None:
            method = Resampling.bilinear
        
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

    def reproject(self, dst_crs, method=None, cell_size=None, unit_factor=None, data_units=None):
        """
        Reproject the raster to a new CRS.

        Parameters
        ----------
        dst_crs : Any
            Target CRS, in any form accepted by rasterio (e.g., WKT,
            PROJ string, EPSG code, or dict).
        method : rasterio.enums.Resampling, default Resampling.nearest
            Resampling algorithm to use during reprojection.
        cell_size : float or tuple, optional
            Target pixel size (in units of ``dst_crs``). If None, a
            default resolution is chosen by
            :func:`rasterio.warp.calculate_default_transform`.
        unit_factor : float, optional
            Multiplicative factor applied to source values before
            reprojection (e.g., ``3600`` to convert in/sec to in/hour).
            Nodata pixels are preserved. When supplied, output dtype is
            promoted to ``float32`` to avoid integer overflow or
            truncation; the source nodata sentinel is carried over
            unchanged. Must be paired with ``data_units``.
        data_units : str, optional
            Data units to assign to the returned grid. Required when
            ``unit_factor`` is supplied, since scaling values changes
            their units. When omitted, the source grid's ``data_units``
            are carried over unchanged.

        Returns
        -------
        RasterSpatialGrid
            New :class:`RasterSpatialGrid` instance in the target CRS,
            with appropriately sized output grid and transform.
        """
        if method is None:
            method = Resampling.nearest

        if unit_factor is not None and data_units is None:
            raise ValueError(
                "data_units is required when unit_factor is set "
                "(scaling values changes their units)."
            )

        src_prof = self.profile
        src_trans = self.transform
        src_width = self.width
        src_height = self.height
        src_crs = self.crs
        src_nodata = self.nodata
        src_data = self.read()
        logging.debug(
            "reproject src: crs=%s transform=%s width=%s height=%s nodata=%s data_shape=%s dtype=%s",
            src_crs, src_trans, src_width, src_height, src_nodata, src_data.shape, src_data.dtype,
        )

        dst_transform, dst_width, dst_height = calculate_default_transform(src_crs, dst_crs, src_width, src_height, *self.bounds, resolution=cell_size)

        # Use a clean GeoTIFF profile for the destination rather than copying src_prof,
        # which may carry source-driver-specific keys (e.g., from GRIB) that are incompatible
        # as a reproject destination.
        dst_prof = DefaultGTiffProfile(count=1)
        dst_prof.update({
            "crs": dst_crs,
            "transform": dst_transform,
            "width": dst_width,
            "height": dst_height,
            "dtype": "float32",
            "nodata": src_nodata,
        })

        if dst_width < 256 or dst_height < 256:
            dst_prof.pop('blockxsize')
            dst_prof.pop('blockysize')

        logging.debug("reproject dst_prof: %s", dst_prof)

        if unit_factor is not None:
            if src_nodata is not None:
                valid = src_data != np.float32(src_nodata)
                src_data[valid] *= unit_factor
            else:
                src_data *= unit_factor

        dst_ds = self._make_rasterio_dataset(None,dst_prof)
        reproject(
            source=src_data,
            destination=rasterio.band(dst_ds, 1),
            src_transform=src_trans,
            src_crs=src_crs,
            src_nodata=src_nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=dst_prof["nodata"],
            resampling=method
        )
        out_data_units = data_units if data_units is not None else self.data_units
        obj = RasterSpatialGrid(dst_ds,data_units=out_data_units,data_type=self.data_type)
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
        if has_gdal:
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

    ds = ogr.Open(shape_file)
    lyr = ds.GetLayer(0)
    shapes = []
    for feat in lyr:
        shape = guard_vector_mask(feat)
        shapes.append(shape)
    return shapes
