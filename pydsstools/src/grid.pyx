# from rasterio
_BoundingBox = namedtuple('BoundingBox', ('left', 'bottom', 'right', 'top'))

_GRID_COMPRESSION_METHODS = {0: 'UNDEFINED', 1: 'UNCOMPRESSED', 26: 'ZLIB DEFLATE' }
_DATA_TYPE = {0: 'PER-AVER', 1: 'PER-CUM', 2: 'INST-VAL', 
              3: 'INST-CUM' , 4: 'FREQ', 5: 'INVALID'}
_DATA_TYPE_INV = {v: k for k, v in _DATA_TYPE.items()}

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
        np.ndarray data

    def __cinit__(self,*arg,**kwargs):
        self.zsgs=NULL
        self._data = None
        self.data = None

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

    cdef int rows(self):
        cdef int num = 0
        if self.zsgs:
            num = self.zsgs[0]._numberOfCellsY
        return num 

    cdef int cols(self):
        cdef int num = 0
        if self.zsgs:
            num = self.zsgs[0]._numberOfCellsX
        return num 

    cdef float cellsize(self):
        cdef float cell_size = 0
        if self.zsgs:
            cell_size = self.zsgs[0]._cellSize
        return cell_size 

    cdef float undefined(self):
        cdef float nd = 0
        if self.zsgs:
            nd = self.zsgs[0]._nullValue
        return nd 

    cdef tuple origin(self):
        cdef: 
            float xmin = UNDEFINED_FLOAT
            float ymin = UNDEFINED_FLOAT
            tuple result

        if self.zsgs:
            xmin = self.zsgs[0]._xCoordOfGridCellZero
            ymin = self.zsgs[0]._yCoordOfGridCellZero

        result = (xmin,ymin)
        return result

    cpdef int structVersion(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._structVersion
        return result

    cpdef int version(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._version
        return result

    cpdef int grid_type(self):
        cdef:
            int result = -9999
        if self.zsgs:
            result = self.zsgs[0]._type
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

        origin = self.origin()
        xmin,ymin = origin

        if not xmin == UNDEFINED_FLOAT:
            rows = self.rows()
            cols = self.cols()
            cell = self.cellsize()
            xmax = xmin + cols*cell
            ymax = ymin + rows*cell

        result = (xmin,xmax,ymin,ymax)
        return result 

    cdef str srs(self):
        cdef:
            char *spatial_reference = NULL
        if self.zsgs:
            spatial_reference = self.zsgs[0]._srsDefinition
            if spatial_reference:
                return spatial_reference
        return ''

    cdef str dataType(self):
        cdef:
            int dtype = NODATA_NEGATIVE 
            char * result = "INVALID"
        if self.zsgs:
            dtype = self.zsgs[0]._dataType
            result = _DATA_TYPE[dtype]
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

    cdef object compressionMethod(self):
        cdef:
            int result = 0
        if self.zsgs:
            result = self.zsgs[0]._compressionMethod
        return _GRID_COMPRESSION_METHODS.get(result,None)

    def _get_data(self, dtype = 'f'):
        cdef:
            int length = self.length()
            view.array mview 
            
        if self.zsgs and self._data is None:    
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
    def _grid_origin(self):
        # native dss array origin
        return "bottom-left corner"

    def read(self,masked=False):
        cdef: 
            int rows
            int cols 
        if self.data is None:
            self._get_data() 
            if not self._data is None:
                rows = self.rows()
                cols = self.cols()
                self.data = np.reshape(self._data,(rows,cols))
                self.data = np.flipud(self.data)
                if not masked:
                    return self.data
                return np.ma.masked_values(self.data,self.undefined())

    property width:
        def __get__(self):
            return self.cols()

    property height:
        def __get__(self):
            return self.rows()

    property transform:
        def __get__(self):
            xmin,xmax,ymin,ymax = self.GetExtents()
            cell = self.cellsize()
            atrans = Affine(cell,0,xmin,0,-cell,ymax)
            return atrans

    property bounds:
        def __get__(self):
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
                           ("Range",self._get_range_limits(num)),
                           ("Greater or Equal Incremental Count",self._get_range_values(num))])
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
    def type (self):
        return self.dataType()
                
    @property
    def nodata (self):
        return self.undefined()

    @property
    def units(self):
        return self.dataUnits()

    @property
    def empty(self):
        if self.zsgs[0]._data:
            False
        return True

    @property
    def profile(self):
        cdef:
            dict result
        result = {'transform':self.transform,
                  'dtype':self.dtype,
                  'nodata':self.nodata,
                  'crs':self.crs,
                  'grid origin':self.grid_origin,
                  'units':self.units,
                  'type':self.type,
                  'compress':self.compressionMethod(),
                  'stats':self.stats}
        return result

    def __dealloc__(self):
        if self.zsgs:
            zstructFree(self.zsgs)

cdef SpatialGridStruct saveSpatialGrid(long long *ifltab, const char* pathname, np.ndarray data, dict profile, int flipud):
    # required args: transform, type, nodata 
    # options args: crs, units, tzid, tzoffset, datasource  
    cdef:
        zStructSpatialGrid *zsgs=NULL
        float[:,::1] _data 
        np.ndarray _data_nan
        int size
        float _min
        float _q1
        float _mean
        float _q3
        float _max
        float _max_int
        float * _pmin = NULL
        float * _pmax = NULL
        float * _pmean = NULL
        float cellsize
        float x,y
        int row,col
        #int * noRLT[2]
        float _nodata
        char * _crs = ""
        char * _units = ""
        char * _type =""
        int _datatype
        char * _datasource
        char * _tzid = ""
        int  _tzoffset = 0
        int range_count = 6
        int range_table_count[6]
        float range_table_value[6]
        #int nodata_count
        int min_count
        int q1_count 
        int mean_count
        int q3_count
        int max_count
        int status
        dict _optional_args = {"tzid":'', "tzoffset":0,
                         "crs":'UNDEFINED',
                         "datasource":'', "units":'UNDEFINED'} 

    for k,v in _optional_args.items():
        try:
            profile[k]
        except:
            profile[k] = v

    zsgs = zstructSpatialGridNew(pathname)
    if flipud:
        data = np.flipud(data)

    data = np.ascontiguousarray(data,dtype=np.float32)


    row = int(data.shape[0])
    col = int(data.shape[1])
    size = row * col

    transform = profile['transform']
    _nodata = profile["nodata"]
    _type = profile["type"]
    _datatype = _DATA_TYPE_INV[_type]
    _tzid = profile["tzid"]
    _tzoffset = profile["tzoffset"]
    _crs = profile['crs']
    _datasource = profile["datasource"]
    _units = profile["units"]

    cellsize = transform[0]
    x = transform[2]
    y = transform[5] - row*cellsize
    _data_nan = np.where(data==_nodata,np.nan,data)
    _max = np.nanmax(_data_nan)
    _min = np.nanmin(_data_nan)
    _mean = np.nanmean(_data_nan)
    _q1 = int(0.5*(_min+_mean))
    _q3 = int(0.5*(_mean+_max))
    _max_int = int(_max)
    
    #nodata_count = np.count_nonzero(~np.isnan(_data_nan))
    min_count = np.count_nonzero(_data_nan >= _min)
    q1_count = np.count_nonzero(_data_nan >= _q1)
    mean_count = np.count_nonzero(_data_nan >= _mean)
    q3_count = np.count_nonzero(_data_nan >= _q3)
    max_count = np.count_nonzero(_data_nan >= _max_int)
    
    _pmax = &_max
    _pmin = &_min
    _pmean = &_mean
    _data = data
    
    range_table_value[:]=[_nodata,_min,_q1,_mean,_q3,_max_int]      
    range_table_count[:]=[size,min_count,q1_count,mean_count,q3_count,max_count]
  
    zsgs[0].pathname  = pathname
    zsgs[0]._structVersion  = -100
    zsgs[0]._type  = 420 # e.g. ALBERS
    zsgs[0]._version  = 1 #0?

    zsgs[0]._dataUnits  = _units
    zsgs[0]._dataType  = _datatype
    zsgs[0]._dataSource  = _datasource
    zsgs[0]._lowerLeftCellX  = 0
    zsgs[0]._lowerLeftCellY  = 0
    zsgs[0]._numberOfCellsX  = <int>col
    zsgs[0]._numberOfCellsY  = <int>row
    zsgs[0]._cellSize  = cellsize
    zsgs[0]._compressionMethod  = 1# 26
    zsgs[0]._compressionParameters  = NULL

    zsgs[0]._srsName  = "" #?
    zsgs[0]._srsDefinitionType  = 0 #?
    zsgs[0]._srsDefinition  = _crs
    zsgs[0]._xCoordOfGridCellZero  = x
    zsgs[0]._yCoordOfGridCellZero  = y
    zsgs[0]._nullValue  = _nodata
    zsgs[0]._timeZoneID  = _tzid
    zsgs[0]._timeZoneRawOffset  = _tzoffset
    zsgs[0]._isInterval  = 0
    zsgs[0]._isTimeStamped  = 0
    zsgs[0]._numberOfRanges  = range_count

    zsgs[0]._storageDataType  = 0
    zsgs[0]._maxDataValue  = <void *>_pmax
    zsgs[0]._minDataValue  = <void *>_pmin
    zsgs[0]._meanDataValue  = <void *>_pmean
    zsgs[0]._rangeLimitTable  = <void *>range_table_value
    zsgs[0]._numberEqualOrExceedingRangeLimit  = <int *>range_table_count
    zsgs[0]._data  = <void *>&_data[0,0]

    status = zspatialGridStore(ifltab,zsgs)

    return 
