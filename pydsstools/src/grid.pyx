# from rasterio
_BoundingBox = namedtuple('BoundingBox', ('left', 'bottom', 'right', 'top'))

GRID_TYPE = {'undefined-time': 400, 'undefined': 401, 
             'hrap-time': 410, 'hrap': 411,
             'shg-time': 420, 'shg': 421,
             'albers-time': 420, 'albers': 421,
             'specified-time': 430, 'specified': 431}
_GRID_TYPE = {v: k for k, v in GRID_TYPE.items()}

GRID_DATA_TYPE = {'per-aver': 0, 'per-cum': 1, 'inst-val': 2, 
                  'inst-cum': 3 , 'freq': 4, 'invalid': 5}
_GRID_DATA_TYPE = {v: k for k, v in GRID_DATA_TYPE.items()}

GRID_COMPRESSION_METHODS = {'undefined': 0, 'uncompressed': 1, 'zlib deflate': 26}
_GRID_COMPRESSION_METHODS = {v: k for k, v in GRID_COMPRESSION_METHODS.items()}


cpdef dict gridInfo():
    info = {}
    info['grid_type'] = 'specified'
    info['grid_crs'] = 'UNDEFINED'
    info['grid_transform'] = None
    info['data_type'] = _GRID_DATA_TYPE[5]
    info['data_units'] = 'UNDEFINED'
    info['opt_crs_name'] = 'WKT'
    info['opt_crs_type'] = 0
    info['opt_compression'] = _GRID_COMPRESSION_METHODS[26]
    info['opt_dtype'] = np.float32
    info['opt_grid_origin'] = 'top-left corner'
    info['opt_data_source'] = ''
    info['opt_tzid'] = 'UTC'
    info['opt_tzoffset'] = 0
    info['opt_is_interval'] = 0
    info['opt_time_stamped'] = 0
    return info

cpdef str gridDataSource(object grid_type):
    #cdef str result
    if isinstance(grid_type,str):
        grid_type = grid_type.lower()
        grid_type = GRID_TYPE.get(grid_type,None)
        if grid_type is None:
            raise Exception('Unknown grid type specified')
    if grid_type == 410 or grid_type == 411:
        result = HRAP_DATASOURCE
    elif grid_type == 420 or grid_type == 421:
        result = SHG_DATASOURCE
    else:
        result = ''
    return result

class BoundingBox(_BoundingBox):
    """Bounding box named tuple, defining extent in cartesian coordinates.
    .. code::
        BoundingBox(left, bottom, right, top)
    Attributes
    ----------
    left :
        Left coordinate
    bottom :
        Bottom coordinate
    right :
        Right coordinate
    top :
        Top coordinate
    """

    def _asdict(self):
        return {*zip(self._fields, self)}

cdef SpatialGridStruct createSGS(zStructSpatialGrid *zsgs):
    sg_st = SpatialGridStruct()
    if zsgs:
        sg_st.zsgs = zsgs
        '''
        if sgs[0].numberValues>=1:
            sg_st.zsgs = sgs
        else:
            zstructFree(sgs)            
            sgs=NULL
        '''
    return sg_st   

cdef void updateSGS(SpatialGridStruct sg_st, zStructSpatialGrid *zsgs):
    if zsgs:
        sg_st.zsgs = zsgs
        '''
        if sgs[0].numberValues>=1:
            sg_st.zsgs = sgs
        else:
            zstructFree(sgs)            
            sgs=NULL
        '''

cdef class SpatialGridStruct:
    cdef:
        zStructSpatialGrid *zsgs
        np.ndarray _data
        #np.ndarray data

    def __cinit__(self,*arg,**kwargs):
        self.zsgs=NULL
        self._data = None
        #self.data = None

    cdef int length(self):
        cdef:
            int rows = 0
            int cols = 0
            int total = 0
        rows = self.rows()
        cols = self.cols()
        total = rows * cols
        return total

    cdef int rangelength(self):
        cdef:
            int length = 0
        if self.zsgs:
            length = self.zsgs[0]._numberOfRanges
        return length

    cdef float undefined(self):
        cdef float nd = 0
        if self.zsgs:
            nd = self.zsgs[0]._nullValue
        return nd 

    cdef int structVersion(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._structVersion
        return result

    cdef int version(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._version
        return result

    cdef int grid_type(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._type
        return result

    cdef str srs(self):
        cdef:
            char *spatial_reference = NULL
        if self.zsgs:
            spatial_reference = self.zsgs[0]._srsDefinition
            if spatial_reference:
                return spatial_reference
        return ''
    
    cdef str srs_name(self):
        cdef char* result = ''
        if self.zsgs:
            result = self.zsgs[0]._srsName
        return result

    cdef int srs_type(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._srsDefinitionType
        return result

    cdef str dataType(self):
        cdef:
            int dtype = NODATA_NEGATIVE 
            char * result = "INVALID"
        if self.zsgs:
            dtype = self.zsgs[0]._dataType
            result = _GRID_DATA_TYPE[dtype]
        return result

    cdef str dataUnits(self):
        cdef:
            char * units = NULL
        if self.zsgs:
            units = self.zsgs[0]._dataUnits
            if units:
                return units
        return ''

    cdef str dataSource(self):
        cdef:
            char * src = NULL
        if self.zsgs:
            src = self.zsgs[0]._dataSource
            if src:
                return src
        return ''

    cdef int storageDataType(self):
        cdef:
            int dtype = NODATA_NEGATIVE 
        if self.zsgs:
            dtype = self.zsgs[0]._storageDataType
        return dtype

    cdef str compressionMethod(self):
        cdef:
            int result = 0
        if self.zsgs:
            result = self.zsgs[0]._compressionMethod
        return _GRID_COMPRESSION_METHODS.get(result)

    cdef str tzid(self):
        cdef char* result = ''
        if self.zsgs:
            result = self.zsgs[0]._timeZoneID
        return result


    cdef int tzoffset(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._timeZoneRawOffset
        return result

    cdef int is_interval(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._isInterval
        return result

    cdef int is_time_stamped(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._isTimeStamped
        return result

    cpdef int rows(self):
        cdef int num = 0
        if self.zsgs:
            num = self.zsgs[0]._numberOfCellsY
        return num 

    cpdef int cols(self):
        cdef int num = 0
        if self.zsgs:
            num = self.zsgs[0]._numberOfCellsX
        return num 

    cpdef float cellsize(self):
        cdef float cell_size = 0
        if self.zsgs:
            cell_size = self.zsgs[0]._cellSize
        return cell_size 


    cpdef tuple origin_coords(self):
        cdef: 
            float xmin = UNDEFINED_FLOAT
            float ymin = UNDEFINED_FLOAT
            tuple result

        if self.zsgs:
            xmin = self.zsgs[0]._xCoordOfGridCellZero
            ymin = self.zsgs[0]._yCoordOfGridCellZero

        result = (xmin,ymin)
        return result


    cpdef tuple GetExtents(self):
        cdef:
            float xmin 
            float ymin
            float xmax = UNDEFINED_FLOAT
            float ymax = UNDEFINED_FLOAT
            float cell
            int rows
            int cols
            tuple origin
            tuple result

        origin = self.origin_coords()
        xmin,ymin = origin

        if not xmin == UNDEFINED_FLOAT:
            rows = self.rows()
            cols = self.cols()
            cell = self.cellsize()
            xmax = xmin + cols*cell
            ymax = ymin + rows*cell

        result = (xmin,xmax,ymin,ymax)
        return result 


    def _get_mview(self, dtype = 'f'):
        cdef:
            int length = self.length()
            view.array mview 

        if not self.zsgs:
            raise print('Empty or Invalid Grid Dataset')
            
        if self._data is None:    
            if self.zsgs[0]._data:
                if dtype == 'f':
                    # no need to allocated because dss using DSS array buffer?
                    mview = view.array(shape=(length,), itemsize=sizeof(float),
                                       format='f', allocate_buffer=False)

                else:
                    mview = view.array(shape=(length,), itemsize=sizeof(double),
                                       format='d', allocate_buffer=False)

                mview.data = <char *>(self.zsgs[0]._data)
                self._data = np.asarray(mview)
                self._data.setflags(write=0)
        return self._data

    def _get_range_limits(self,array_length, dtype='f'):
        cdef: 
            int length = array_length
            view.array mview 
            
        if self.zsgs:
            if self.zsgs[0]._rangeLimitTable: 
                mview = view.array(shape=(length,),itemsize=sizeof(float),
                                   format='%s'%dtype,allocate_buffer=False)
                mview.data = <char *>(self.zsgs[0]._rangeLimitTable)
                return np.asarray(mview)

    def _get_range_values(self,array_length):
        cdef: 
            int length = array_length
            view.array mview 
            
        if self.zsgs:
            if self.zsgs[0]._numberEqualOrExceedingRangeLimit: 
                mview = view.array(shape=(length,),itemsize=sizeof(int),format='i',
                                   allocate_buffer=False)
                mview.data = <char *>(self.zsgs[0]._numberEqualOrExceedingRangeLimit)
                return np.asarray(mview)


    @property
    def native_grid_origin(self):
        # native dss array origin
        return "bottom-left corner"

    def read(self):
        cdef: 
            int rows
            int cols 
        self._get_mview() 
        rows = self.rows()
        cols = self.cols()
        data = np.reshape(self._data,(rows,cols))
        data = np.flipud(data)
        return np.ma.masked_values(data,self.undefined())

    @property
    def width(self):
        return self.cols()

    @property
    def height(self):
        return self.rows()

    @property
    def transform(self):
        xmin,xmax,ymin,ymax = self.GetExtents()
        cell = self.cellsize()
        atrans = Affine(cell,0,xmin,0,-cell,ymax)
        return atrans

    @property
    def bounds(self):
        cdef float xmin,xmax,ymin,ymax
        xmin,xmax,ymin,ymax = self.GetExtents()
        return BoundingBox(xmin,ymin,xmax,ymax)


    @property
    def grid_origin(self):
        return "top-left corner"

    @property
    def stats(self):
        cdef:
            float * _max = NULL 
            float * _min = NULL 
            float * _mean = NULL
            float  maxval = UNDEFINED_FLOAT 
            float  minval = UNDEFINED_FLOAT 
            float  meanval = UNDEFINED_FLOAT
            int num = 0
            dict result

        result = {}
        if self.zsgs:
            _max = <float *>self.zsgs[0]._maxDataValue
            _min = <float *>self.zsgs[0]._minDataValue
            _mean = <float *>self.zsgs[0]._meanDataValue
            if _max: maxval = _max[0]
            if _min: minval = _min[0]
            if _mean: meanval = _mean[0]
            num = self.rangelength()
            result.update([("min",minval),
                           ("max",maxval),
                           ("mean",meanval),
                           ("range_values",self._get_range_limits(num).tolist()),
                           ("range_counts",self._get_range_values(num).tolist())])
        return result

    @property
    def crs(self):
        return self.srs()

    @property
    def interval(self):
        return self.cellsize()


    @property
    def dtype (self):
        return np.float32

    @property
    def data_type (self):
        return self.dataType()
                
    @property
    def nodata (self):
        return self.undefined()

    @property
    def units(self):
        return self.dataUnits()

    @property
    def profile(self):
        cdef:
            dict result
        result = gridInfo()
        result.update([('grid_type',_GRID_TYPE[self.grid_type()]), 
                       ('grid_crs',self.srs()),
                       ('grid_transform',self.transform),
                       ('data_type',self.dataType()),
                       ('data_units',self.dataUnits()),
                       ('opt_compression',self.compressionMethod()),
                       ('opt_dtype',self.dtype),
                       ('opt_data_source',self.dataSource()),
                       ('opt_grid_origin',self.grid_origin),
                       ('opt_crs_name',self.srs_name()),
                       ('opt_crs_type',self.srs_type()),
                       ('opt_tzid',self.tzid()),
                       ('opt_tzoffset',self.tzoffset()),
                       ('opt_is_interval',True if self.is_interval() else False),
                       ('opt_time_stamped',True if self.is_time_stamped() else False),
                       ])
        return result

    def __dealloc__(self):
        if self.zsgs:
            zstructFree(self.zsgs)

cdef SpatialGridStruct saveSpatialGrid(long long *ifltab, const char* pathname, np.ndarray data, float nodata, dict stats, dict profile):
    cdef:
        zStructSpatialGrid *zsgs=NULL
        float[:,::1] _data 
        #np.ndarray data
        int _row,_col
        float _x,_y
        float _nodata
        float * _pmin = NULL
        float * _pmax = NULL
        float * _pmean = NULL
        char * _crs = ""
        char * _crs_name = ""
        int _crs_type = 0
        char * _units = ""
        int _type
        int _datatype
        char * _datasource= ""
        char * _tzid = ""
        int  _tzoffset = 0
        int _is_interval = 0
        int _time_stamped = 0
        int _range_count = 0
        int _range_table_counts[20]
        float _range_table_values[20]
        int _compression_method
        float cellsize
        float _min,_max,_mean
        list range_values, range_counts
        object transform
        int status
        int i,rc
        float rv

    zsgs = zstructSpatialGridNew(pathname)

    data = np.ascontiguousarray(data,dtype=np.float32)
    _row = int(data.shape[0])
    _col = int(data.shape[1])

    _nodata = <float>nodata
    _type = GRID_TYPE[profile['grid_type']] # int
    _datatype = GRID_DATA_TYPE[profile['data_type']] # int
    _tzid = profile['opt_tzid'] #str
    _tzoffset = profile['opt_tzoffset'] #int
    _crs = profile['grid_crs'] #str
    _crs_name = profile['opt_crs_name'] #str
    _crs_type = profile['opt_crs_type'] #int
    _datasource = profile['opt_data_source'] # str
    _units = profile['data_units'] #str
    _is_interval = profile['opt_is_interval']
    _time_stamped = profile['opt_time_stamped']

    transform = profile['grid_transform']
    cellsize = transform[0]
    _x = transform[2]
    _y = transform[5] - _row*cellsize
    
    _min = stats['min']
    _max = stats['max']
    _mean = stats['mean']
    _pmin = &_min
    _pmax = &_max
    _pmean = &_mean
    _data = data
    
    range_values = stats['range_values']
    range_counts = stats['range_counts']
    _range_count = min(len(stats['range_values']),20)
    for i in range(0,_range_count):
        rv = <float>range_values[i]
        rc = <int>range_counts[i]
        _range_table_values[i]= rv     
        _range_table_counts[i]= rc

    _compression_method = GRID_COMPRESSION_METHODS[profile['opt_compression']]
  
    zsgs[0].pathname  = pathname
    zsgs[0]._structVersion  = -100 # DSS-7
    zsgs[0]._type  = _type
    zsgs[0]._version  = 1 # ???

    zsgs[0]._dataUnits  = _units
    zsgs[0]._dataType  = _datatype
    zsgs[0]._dataSource  = _datasource
    zsgs[0]._lowerLeftCellX  = 0
    zsgs[0]._lowerLeftCellY  = 0
    zsgs[0]._numberOfCellsX  = <int>_col
    zsgs[0]._numberOfCellsY  = <int>_row
    zsgs[0]._cellSize  = cellsize
    zsgs[0]._compressionMethod  = _compression_method
    zsgs[0]._compressionParameters  = NULL

    zsgs[0]._srsName  = _crs_name
    zsgs[0]._srsDefinitionType  = _crs_type
    zsgs[0]._srsDefinition  = _crs
    zsgs[0]._xCoordOfGridCellZero  = _x
    zsgs[0]._yCoordOfGridCellZero  = _y
    zsgs[0]._nullValue  = _nodata
    zsgs[0]._timeZoneID  = _tzid
    zsgs[0]._timeZoneRawOffset  = _tzoffset
    zsgs[0]._isInterval  = _is_interval
    zsgs[0]._isTimeStamped  = _time_stamped
    zsgs[0]._numberOfRanges  = _range_count

    zsgs[0]._storageDataType  = 0
    zsgs[0]._maxDataValue  = <void *>_pmax
    zsgs[0]._minDataValue  = <void *>_pmin
    zsgs[0]._meanDataValue  = <void *>_pmean
    zsgs[0]._rangeLimitTable  = <void *>_range_table_values
    zsgs[0]._numberEqualOrExceedingRangeLimit  = <int *>_range_table_counts
    zsgs[0]._data  = <void *>&_data[0,0]

    status = zspatialGridStore(ifltab,zsgs)

    return 
