from .._lib import SpatialGridStruct as _SpatialGridStruct
from .transform import TransformMethodsMixin

class SpatialGridStruct(_SpatialGridStruct,TransformMethodsMixin):
    _accessors = set()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._crs = '' # private variable for use by raster accessor
