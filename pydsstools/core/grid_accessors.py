import logging
from .transform import Affine, from_bounds, from_origin
from .accessors import register_grid_accessor

try:
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.crs import CRS
    from rasterio.plot import show as _show # matplotlib?
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
            return profile

        def _data(self):
            data = self._obj._get_mview()    
            data.setflags(write=1) # need to review this
            data = np.reshape(data,(self._obj.height,self._obj.width))
            return data

        def _resample(self, out_transform = None, crs = None, method = Resampling.bilinear):
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
                      src_crs = crs,
                      dst_crs = crs,
                      resampling = method,
                      warp_mem_limit = 64)
            return out_data

        def _contours(self,**kwargs):
            #contourInterval = kwargs.get('contourInterval',None) # float
            #contourBase = kwargs.get('contourBase',None) # int
            #fixedLevelCount = kwargs.get('fixedLevelCount',None) # list
            #useNoData = kwargs.get('useNoData',None) # int
            #noDataValue, = kwargs.get('noDataValue',None) # float
            #dstLayer = kwargs.get('dstLayer',None) # shapefile layer
            #idField = kwargs.get('idField',None) # shp column no for field
            #elevField = kwargs.get('elevField',None) # shp column no for elev
            # gdal.ContourGenerate(srcBand,0.1,0,[0.0],0,NODATA,contour_shp, 0,1) # example            
            return NotImplemented

        def save_tiff(self, filepath, crs = None, update_profile = None):
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

            _crs = profile['crs']
            if not crs is None:
                _crs = crs

            if isinstance(_crs,int):
                profile['crs'] = CRS.from_epsg(_crs)

            with rasterio.open(filepath,'w', **profile) as dst:
                dst.write(data,1)

        def plot(self):
            data = self._obj.read()
            # TODO: Correct plotted axis range
            _show(data)



