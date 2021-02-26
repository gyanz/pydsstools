from .._lib import SpatialGridStruct as _SpatialGridStruct
from .transform import TransformMethodsMixin

class SpatialGridStruct(_SpatialGridStruct,TransformMethodsMixin):
    _accessors = set()
