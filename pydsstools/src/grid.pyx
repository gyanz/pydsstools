# from rasterio
_BoundingBox = namedtuple('BoundingBox', ('left', 'bottom', 'right', 'top'))

GRID_TYPE = {'undefined-time': 400, 'undefined': 401, 
             'hrap-time': 410, 'hrap': 411,
             'albers-time': 420, 'albers': 421,
             'shg-time': 420, 'shg': 421,
             'specified-time': 430, 'specified': 431}
_GRID_TYPE = {v: k for k, v in GRID_TYPE.items() if not k in ('shg','shg-time')}

GRID_DATA_TYPE = {'per-aver': 0, 'per-cum': 1, 'inst-val': 2, 
                  'inst-cum': 3 , 'freq': 4, 'invalid': 5}
_GRID_DATA_TYPE = {v: k for k, v in GRID_DATA_TYPE.items()}

GRID_COMPRESSION_METHODS = {'undefined': 0, 'uncompressed': 1, 'zlib deflate': 26}
_GRID_COMPRESSION_METHODS = {v: k for k, v in GRID_COMPRESSION_METHODS.items()}

cpdef dict gridInfo():
    info = {}
    info['grid_type'] = 'specified'
    info['grid_crs'] = 'UNDEFINED' #WKT
    info['grid_transform'] = None
    info['data_type'] = _GRID_DATA_TYPE[5]
    info['data_units'] = 'UNDEFINED'
    info['opt_crs_name'] = 'UNDEFINED'
    info['opt_crs_type'] = 0 #WKT = 0
    info['opt_compression'] = _GRID_COMPRESSION_METHODS[26]
    info['opt_dtype'] = np.float32
    info['opt_grid_origin'] = 'top-left corner'
    info['opt_data_source'] = '' # used with HRAP
    info['opt_tzid'] = 'UTC'
    info['opt_tzoffset'] = 0
    info['opt_is_interval'] = 0
    info['opt_time_stamped'] = 0
    info['opt_lower_left_x'] = 0
    info['opt_lower_left_y'] = 0
    info['opt_cell_zero_xcoord'] = 0
    info['opt_cell_zero_ycoord'] = 0
    return info

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

HEC_SHG_CELLSIZE = (10000,5000,2000,1000,500,200,100,50,20,10) # meters
HEC_SHG_APART = ('SHG10K','SHG5K','SHG2K','SHG1K','SHG500','SHG200','SHG100','SHG50','SHG20','SHG10') # meters

def check_shg_gridinfo(gridinfo):
    issue = 0
    if gridinfo['grid_type'].lower() not in ('albers','albers-time','shg','shg-time'):
        logging.warn('Invalid grid_type')
        issue += 1
    if gridinfo['grid_crs'] != SHG_WKT:
        logging.warn('Invalid grid_crs')
        issue += 1
    cellsize = gridinfo['grid_transform'][0]
    if not cellsize in HEC_SHG_CELLSIZE: 
        logging.warn('Not an standard cellsize for SHG grid')
        issue += 1
    if not gridinfo['opt_crs_name'] in ('SHG','shg'):
        logging.info('Recommended opt_crs_name is SHG or shg')
        issue += 1
    return issue

def correct_shg_gridinfo(gridinfo,shape):
    gridinfo = gridinfo.copy()
    if gridinfo['grid_type'].lower() not in ('albers','albers-time','shg','shg-time'):
        raise Exception('Invalid grid_type')
    if gridinfo['grid_crs'] != SHG_WKT:
        gridinfo['grid_crs'] = SHG_WKT
    trans = gridinfo['grid_transform']
    cellsize = trans[0]
    if not cellsize in HEC_SHG_CELLSIZE: 
        raise Exception('Not an standard cellsize for SHG grid. Use one of thes sizes %r in meters'%HEC_SHG_CELLSIZE)
    gridinfo['opt_crs_name'] = 'AlbersInfo'
    if gridinfo['grid_type'].lower().startswith('shg'):
        gridinfo['opt_crs_name'] = 'SHG'
    lower_left_x, lower_left_y = lower_left_xy_from_transform(trans,shape,
                                                              gridinfo['opt_cell_zero_xcoord'],
                                                              gridinfo['opt_cell_zero_ycoord'])
    gridinfo['opt_lower_left_x'] = lower_left_x
    gridinfo['opt_lower_left_y'] = lower_left_y
    return gridinfo

def lower_left_xy_from_transform(transform,shape,cell_zero_xcoord=0,cell_zero_ycoord=0):
    cdef:
        float xmin,ymax
        float ymin # verbose to make calculation more clear
        int lower_left_x,lower_left_y
    cellsize = transform[0]
    cellsize_y = transform[4]
    rows,cols = shape
    xmin = transform[2] - cell_zero_xcoord
    ymax = transform[5] - cell_zero_ycoord
    ymin = ymax + rows * cellsize_y
    lower_left_x = <int>(floor(xmin/cellsize))
    lower_left_y = <int>(floor(ymax/cellsize))
    return (lower_left_x,lower_left_y)

cdef SpatialGridStruct createSGS(zStructSpatialGrid *zsgs):
    sg_st = SpatialGridStruct()
    if zsgs:
        sg_st.zsgs = zsgs
    return sg_st   

cdef void updateSGS(SpatialGridStruct sg_st, zStructSpatialGrid *zsgs):
    if zsgs:
        sg_st.zsgs = zsgs

cdef class SpatialGridStruct:
    cdef:
        zStructSpatialGrid *zsgs
        np.ndarray _data

    def __cinit__(self,*arg,**kwargs):
        self.zsgs=NULL
        self._data = None

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
            int result = 401 # undefined
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

    cpdef int lower_left_x(self):
        cdef int llx = 0
        if self.zsgs:
            llx = self.zsgs[0]._lowerLeftCellX
        return llx

    cpdef int lower_left_y(self):
        cdef int lly = 0
        if self.zsgs:
            lly = self.zsgs[0]._lowerLeftCellY
        return lly

    cpdef tuple GetExtents(self):
        cdef:
            float xorig 
            float yorig
            float xmin 
            float ymin
            float xmax = UNDEFINED_FLOAT
            float ymax = UNDEFINED_FLOAT
            float cell
            int rows, row_bottom
            int cols, col_bottom
            tuple origin
            tuple result

        origin = self.origin_coords()
        xorig,yorig = origin
        col_bottom = self.lower_left_x()
        row_bottom = self.lower_left_y()

        if not xorig == UNDEFINED_FLOAT:
            rows = self.rows()
            cols = self.cols()
            cell = self.cellsize()
            xmin = xorig + col_bottom * cell
            ymin = yorig + row_bottom * cell
            xmax = xmin + cols * cell
            ymax = ymin + rows * cell

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

    def stats(self,trim=True):
        cdef:
            float * _max = NULL 
            float * _min = NULL 
            float * _mean = NULL
            float  maxval = UNDEFINED_FLOAT 
            float  minval = UNDEFINED_FLOAT 
            float  meanval = UNDEFINED_FLOAT
            int i, num = 0
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
            range_values = self._get_range_limits(num).tolist()
            range_counts = self._get_range_values(num).tolist()
            last_index = num
            if trim:
                # remove multiple bins with 0 counts
                for i,count in enumerate(range_counts,1):
                    if count == 0:
                        last_index = i
                        break
            result.update([("min",minval),
                           ("max",maxval),
                           ("mean",meanval),
                           ("range_values",range_values[0:last_index]),
                           ("range_counts",range_counts[0:last_index])])
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
                       ('opt_lower_left_x',self.lower_left_x()),
                       ('opt_lower_left_y',self.lower_left_y()),
                       ('opt_cell_zero_xcoord',self.origin_coords()[0]),
                       ('opt_cell_zero_ycoord',self.origin_coords()[1]),
                       ])
        return result

    def __dealloc__(self):
        if self.zsgs:
            zstructFree(self.zsgs)

cdef int saveSpatialGrid(long long *ifltab, const char* pathname, np.ndarray data, float nodata, dict stats, dict profile):
    cdef:
        zStructSpatialGrid *zsgs=NULL
        float[:,::1] _data 
        int _row,_col
        float _x,_y
        int _lower_left_x, _lower_left_y
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
    #cellsize_y = transform[4]
    #_x = transform[2]
    #_y = transform[5] + _row*cellsize_y
    _x = profile['opt_cell_zero_xcoord']
    _y = profile['opt_cell_zero_ycoord']

    _lower_left_x = profile['opt_lower_left_x']
    _lower_left_y = profile['opt_lower_left_y']
    
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
    zsgs[0]._lowerLeftCellX  = _lower_left_x
    zsgs[0]._lowerLeftCellY  = _lower_left_y
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

    return status 
