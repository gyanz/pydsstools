from .accessors import register_grid_accessor

try:
    import rasterio
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.crs import CRS
    from rasterio.plot import show as _show # matplotlib dependent?
    import numpy as np
except:
    print('Missing rasterio library ...')
    print('Raster accessor for spatial grid not available.')
else:
    @register_grid_accessor("raster")
    class RasterioAccessor:
        def __init__(self, grid_struct):
            self._obj = grid_struct

        def save_tiff(self, filepath, crs = None, update_profile = None):
            # grid_crs in grid dataset is optional and can't be relied upon
            # crs is string (proj4, wkt, etc.) or int (epsg code) argument
            # crs provided via update_profile argument is ignored when crs argument is not None
            data = self._obj._get_mview()    
            data.setflags(write=1)
            row = self._obj.height
            col = self._obj.width
            data = np.reshape(data,(row,col))
            # prepare rasterio profile
            gridinfo = self._obj.profile
            profile = DefaultGTiffProfile(count = 1)
            profile['transform'] = gridinfo['grid_transform']
            profile['dtype'] = 'float32' # TODO: select float32 and float64 based on grid dtype
            profile['nodata'] = self._obj.nodata
            profile['height'] = row
            profile['width'] = col
            profile['crs'] = gridinfo['grid_crs']

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
            # TODO: Correct axis values
            _show(data)

