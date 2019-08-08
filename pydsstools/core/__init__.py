__all__ = ['core_heclib',
           'UNDEFINED',
           'Open',
           'TimeSeriesContainer',
           'TimeSeriesStruct', #can't use this from python directly
           'PairedDataContainer',
           'PairedDataStruct', #can't use this from python directly
           'SpatialGridStruct',
           'getPathnameCatalog',
           'deletePathname',
           'dss_info',
           'HecTime',
           'DssPathName',
           'DssStatusException',
           'GranularityException',
           'ArgumentException',
           'DssLastError']


from .._lib import *
