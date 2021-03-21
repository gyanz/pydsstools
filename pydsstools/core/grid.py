import numpy as np
import numpy.ma as ma
from .._lib import SpatialGridStruct as SpatialGridStructBase
from .transform import TransformMethodsMixin, array_bounds

class SpatialGridStruct(SpatialGridStructBase,TransformMethodsMixin):
    _accessors = set()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._crs = '' # private variable for use by raster accessor

class _SpatialGridStruct(SpatialGridStruct):
    """ Private class that acts like SpatialGridStuct used to wrap raster dataset
    """
    def __init__(self,data,grid_info):
        self._gridinfo = {key:val for key,val in grid_info.items()}
        self._data = {}
        if isinstance(data,ma.core.MaskedArray):
            self._data['data'] = data
        elif isinstance(data,np.ndarray):
            self._data['data'] = ma.masked_values(data,np.nan)
        else:
            raise Exception('Invalid data. It must be ndarray or masked array')
        print(data.shape)
        rows,cols = data.shape
        self._data['width'] = cols
        self._data['height'] = rows
        self._crs = self._gridinfo['grid_crs']

    def cellsize(self):
        return self.transform.xoff

    def origin_coords(self):
        xmin,xmax,ymin,ymax = self.GetExtents()
        return (xmin,ymin)

    def lower_left_x(self):
        extent = self.GetExtents()
        return extent[0]

    def lower_left_y(self):
        extent = self.GetExtents()
        return extent[2]

    def GetExtents(self):
        trans = self.transform
        width = self.width
        height = self.height
        xmin,ymin,xmax,ymax = array_bounds(height,width,trans)
        return (xmin,xmax,ymin,ymax)

    def _get_mview(self, dtype = 'f'):
        data = np.flipud(self._data['data']._data.copy())  
        return data

    def read(self):
        return self._data.get('data',None)

    @property
    def width(self):
        return self._data.get('width',None)

    @property
    def height(self):
        return self._data.get('height',None)

    @property
    def transform(self):
        return self._gridinfo.get('grid_transform',None )  

    @property
    def stats(self):
        # delegate stats computation to put_grid method
        # while saving to dss file
        # put_grid method will recompute stats if stats is empy or null equivalent value
        return {}

    @property
    def crs(self):
        return self._gridinfo.get('grid_crs',None )  

    @property
    def interval(self):
        return self.cellsize()

    @property
    def data_type(self):
        return self._gridinfo.get('data_type',None)  

    @property
    def nodata(self):
        return self._data['data'].fill_value

    @property
    def units(self):
        return self._gridinfo.get('grid_units','')  
    
    @property
    def profile(self):
        return self._gridinfo.copy()










































