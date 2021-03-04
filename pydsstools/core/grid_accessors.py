import logging
from .transform import Affine, from_bounds, from_origin
from .accessors import register_grid_accessor

try:
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.crs import CRS
    from rasterio.plot import show as _show # matplotlib?
    import gdal
    gdal.UseExceptions()
    import ogr
    import numpy as np
except:
    logging.debug('Missing rasterio library ...')
    logging.debug('Raster accessor for spatial grid not available.')
else:
    logging.info('Registering raster accessor for SpatialGridStruct')
    @register_grid_accessor("raster")
    class RasterAccessor:
        def __init__(self, grid_struct):
            self._obj = grid_struct

        def define_crs(self,crs):
            """ Define crs once for the grid. This crs overides grid_crs during raster analysis. 
            """
            try:
                crs = int(crs)
            except:
                pass
            if isinstance(crs,int):
                crs = CRS.from_epsg(crs)
            else:
                crs = CRS.from_string(crs)
            # crs as WKT
            self._obj._crs = crs.to_wkt()

        def _default_rasterio_profile(self):
            # prepare rasterio profile
            row = self._obj.height
            col = self._obj.width
            gridinfo = self._obj.profile
            profile = DefaultGTiffProfile(count = 1)
            if row < 256 or col < 256:
                profile.pop('blockxsize')
                profile.pop('blockysize')
            profile['transform'] = gridinfo['grid_transform']
            profile['dtype'] = 'float32' # TODO: select float32 and float64 based on grid dtype
            profile['nodata'] = self._obj.nodata
            profile['height'] = row
            profile['width'] = col
            profile['crs'] = gridinfo['grid_crs']
            if self._obj._crs:
                profile['crs'] = self._obj._crs
            else:
                logging.warn('CRS has not been defined for the grid dataset for raster processing')
            return profile

        def _data(self):
            data = self._obj._get_mview()    
            data.setflags(write=1) # need to review this
            data = np.reshape(data,(self._obj.height,self._obj.width))
            return data

        def _as_raster_datasource(self):
            # create in-memory gdal raster source
            prof = self._default_rasterio_profile()
            driver = gdal.GetDriverByName('MEM')
            ds = driver.Create('',self._obj.width,self._obj.height,1,6) # GDT_Float32 = 6
            ds.SetProjection(prof['crs']) # WKT
            ds.SetGeoTransform(Affine.to_gdal(prof['transform']))
            srcband = ds.GetRasterBand(1)
            srcband.WriteArray(self._data())
            return ds


        def _resample(self, out_transform = None, method = Resampling.bilinear):
            # private method 
            # returns resampled array data based
            # default resampling method is bilinear
            prof = self._default_rasterio_profile()
            out_data = np.empty((prof['height'],prof['width']),np.float32)
            # TODO: Compare out_transform with grid's transform
            # returns grid's buffer skipping reprojection if they are equal
            # raise exception if they do not have common space
            reproject(self._data(), out_data,
                      src_nodata = prof['nodata'],
                      dst_nodata = prof['nodata'],
                      src_transform = prof['transform'],
                      dst_transform = out_transform,
                      src_crs = prof['crs'],
                      dst_crs = prof['crs'],
                      resampling = method,
                      warp_mem_limit = 64)
            return out_data

        def generate_contours(self,shape_file,**kwargs):
            """ Generate contour shapefile using GDALContourGenerate

            Parameters:
                shape_file: str
                            path of output contour shapefile

                base: float, default 0 
                      base relative to which contour intervals are generated

                interval: float, default 10
                          elevation interval between generated contours

                fixed_levels: list, default []
                              List of elevations at which additional
                              contours are generated

                ignore_nodata: bool, default True
                               flag to ignore nodata pixel during contour generation
            """
            interval = kwargs.get('interval', 10)
            base = kwargs.get('base', 0)
            fixed_levels = kwargs.get('fixed_levels', [])
            ignore_nodata = kwargs.get('ignore_nodata', True)
            # grid profile
            prof = self._default_rasterio_profile()
            # create in-memory gdal raster source
            ds1 = self._as_raster_datasource()
            srcband = ds1.GetRasterBand(1)
            # create contour shape file
            crs = ogr.osr.SpatialReference()
            crs.ImportFromWkt(prof['crs'])
            ds2 = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shape_file)
            contour_layer = ds2.CreateLayer('contour',crs,ogr.wkbMultiLineString)
            field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
            contour_layer.CreateField(field_defn)
            field_defn = ogr.FieldDefn("ELEV", ogr.OFTReal)
            contour_layer.CreateField(field_defn)
            # contouring method
            use_nodata = 0 if ignore_nodata else 1
            gdal.ContourGenerate(srcband,interval,base,         # interval, base
                                 fixed_levels,                  # fixedlevelcount list
                                 use_nodata, prof['nodata'] ,   # usenodata, nodata
                                 contour_layer,                 # dstlayer 
                                 0,1)                           # ID field, ELEV field


        def save_tiff(self, filepath, update_profile = None):
            # grid_crs in grid dataset is optional and can't be relied upon
            # crs is string (proj4, wkt, etc.) or int (epsg code) argument
            # crs provided via update_profile argument is ignored when crs argument is not None
            data = self._data()
            # prepare rasterio profile
            profile = self._default_rasterio_profile()

            # TODO: perform check if grid_crs value is valid value
            # Print warning message when grid_crs is valid but crs value provided through arguments
            if isinstance(update_profile,(dict,DefaultGTiffProfile)):
                for k in update_profile:
                    profile[k] = update_profile[k]

            with rasterio.open(filepath,'w', **profile) as dst:
                dst.write(data,1)

        def plot(self):
            data = self._obj.read()
            # TODO: Correct plotted axis range
            _show(data)



