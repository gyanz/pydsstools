GRID_TYPE = {'undefined-time': 400, 'undefined': 401, 
             'hrap-time': 410, 'hrap': 411,
             'albers-time': 420, 'albers': 421,
             'shg-time': 420, 'shg': 421,
             'specified-time': 430, 'specified': 431
}

_GRID_TYPE = {v: k for k, v in GRID_TYPE.items() if not k in ('shg','shg-time')}

GRID_DATA_TYPE = {'per-aver': 0, 'per-cum': 1, 'inst-val': 2, 
                  'inst-cum': 3 , 'freq': 4, 'invalid': 5
}
_GRID_DATA_TYPE = {v: k for k, v in GRID_DATA_TYPE.items()}

GRID_COMPRESSION_METHODS = {'undefined': 0, 'uncompressed': 1, 'zlib deflate': 26}
_GRID_COMPRESSION_METHODS = {v: k for k, v in GRID_COMPRESSION_METHODS.items()}

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

    def __dealloc__(self):
        if self.zsgs:
            zstructFree(self.zsgs)

    cdef str _pathname(self):
        cdef char* result = ''
        if self.zsgs:
            result = self.zsgs[0].pathname
        return result

    cdef int size(self):
        cdef:
            int rows = 0
            int cols = 0
            int total = 0
        rows = self.rows()
        cols = self.cols()
        total = rows * cols
        return total

    cdef int numberOfRanges(self):
        cdef:
            int length = 0
        if self.zsgs:
            length = self.zsgs[0]._numberOfRanges
        return length

    cdef float nullValue(self):
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

    cdef str srs_name(self):
        cdef char* result = ''
        if self.zsgs:
            result = self.zsgs[0]._srsName
        return result

    cdef str srs_definition(self):
        cdef:
            char *spatial_reference = NULL
        if self.zsgs:
            spatial_reference = self.zsgs[0]._srsDefinition
            if spatial_reference:
                return spatial_reference
        return ''

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

    cdef float cellSize(self):
        cdef float cell_size = 0
        if self.zsgs:
            cell_size = self.zsgs[0]._cellSize
        return cell_size 

    cdef int compressionMethod(self):
        cdef:
            int result = 0
        if self.zsgs:
            result = self.zsgs[0]._compressionMethod
        return result

    cdef int sizeOfCompressedElements(self):
        cdef:
            int int = 0
        if self.zsgs:
            result = self.zsgs[0]._sizeofCompressedElements
        return result

    cdef str timeZoneID(self):
        cdef char* result = ''
        if self.zsgs:
            result = self.zsgs[0]._timeZoneID
        return result

    cdef int timeZoneRawOffset(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._timeZoneRawOffset
        return result

    cdef int isInterval(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._isInterval
        return result

    cdef int isTimeStamped(self):
        cdef int result = 0
        if self.zsgs:
            result = self.zsgs[0]._isTimeStamped
        return result

    cdef tuple cell0_coords(self):
        cdef: 
            float xmin = UNDEFINED_FLOAT
            float ymin = UNDEFINED_FLOAT
            tuple result

        if self.zsgs:
            xmin = self.zsgs[0]._xCoordOfGridCellZero
            ymin = self.zsgs[0]._yCoordOfGridCellZero

        result = (xmin,ymin)
        return result

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

    cdef int lower_left_x(self):
        cdef int llx = 0
        if self.zsgs:
            llx = self.zsgs[0]._lowerLeftCellX
        return llx

    cdef int lower_left_y(self):
        cdef int lly = 0
        if self.zsgs:
            lly = self.zsgs[0]._lowerLeftCellY
        return lly

    cdef float maxDataValue(self):
        cdef:
            float * _val = NULL 
            float  val = UNDEFINED_FLOAT 

        if self.zsgs:
            _val = <float *>self.zsgs[0]._maxDataValue
            if _val: val = _val[0]
        return val    

    cdef float minDataValue(self):
        cdef:
            float * _val = NULL 
            float  val = UNDEFINED_FLOAT 

        if self.zsgs:
            _val = <float *>self.zsgs[0]._minDataValue
            if _val: val = _val[0]
        return val    

    cdef float meanDataValue(self):
        cdef:
            float * _val = NULL 
            float  val = UNDEFINED_FLOAT 

        if self.zsgs:
            _val = <float *>self.zsgs[0]._meanDataValue
            if _val: val = _val[0]
        return val    

    cpdef tuple get_extents(self):
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

        result = ()
        origin = self.cell0_coords()
        xorig,yorig = origin
        col_ll = self.lower_left_x()
        row_ll = self.lower_left_y()

        if not xorig == UNDEFINED_FLOAT:
            rows = self.rows()
            cols = self.cols()
            cell = self.cellSize()
            xmin = xorig + col_ll * cell
            ymin = yorig + row_ll * cell
            xmax = xmin + cols * cell
            ymax = ymin + rows * cell
            result = (xmin,xmax,ymin,ymax)

        return result 

    cpdef tuple get_min_xy(self):
        cdef:
            float xmin,ymin

        result = self.get_extents()
        if result:
            return (result[0],result[2])
        return ()

    def _get_mview(self, dtype = 'f'):
        cdef:
            int length = self.size()
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

    def read(self):
        cdef:
            int rows, cols
        self._get_mview() 
        rows = self.rows()
        cols = self.cols()
        data = np.reshape(self._data,(rows,cols))
        data = np.flipud(data)
        return np.ma.masked_values(data,self.nullValue())

    # ===============================
    # Python accessible attributes
    # ===============================
    @property
    def grid_type (self):
        num = self.grid_type()
        return _GRID_TYPE[num]

    @property
    def grid_type2 (self):
        num = self.grid_type()
        return num

    @property
    def dtype (self):
        return np.float32

    @property
    def pathname(self):
        return self._pathname()

    @property
    def data_source(self):
        return self.dataSource()

    @property
    def data_units(self):
        return self.dataUnits()

    @property
    def data_type (self):
        return self.dataType()
    
    @property
    def lower_left_cell(self):
        return (self.lower_left_x(), self.lower_left_y())

    @property
    def cols(self):
        # width
        return self.cols()

    @property
    def rows(self):
        # height
        return self.rows()

    @property
    def cell_size(self):
        return self.cellSize()

    @property
    def compression_method(self):    
        result = self.compressionMethod()
        return _GRID_COMPRESSION_METHODS[result]

    @property
    def compression_method2(self):    
        result = self.compressionMethod()
        return result

    @property
    def compression_size(self):    
        return self.sizeOfCompressedElements()

    @property
    def compression_base(self):
        return 0

    @property
    def compression_factor(self):
        return 0

    @property
    def crs(self):
        return self.srs_definition()

    @property
    def crs_name(self):
        return self.srs_name()

    @property
    def crs_type(self):
        return self.srs_type()

    @property
    def coords_cell0(self):
        return self.cell0_coords()
                
    @property
    def nodata (self):
        return self.nullValue()

    @property
    def tzid (self):
        return self.timeZoneID()

    @property
    def tzoffset (self):
        return self.timeZoneRawOffset()

    @property
    def is_interval (self):
        return self.isInterval()

    @property
    def time_stamped (self):
        return self.isTimeStamped()

    @property
    def max_val (self):
        return self.maxDataValue()

    @property
    def min_val (self):
        return self.minDataValue()

    @property
    def mean_val (self):
        return self.meanDataValue()

    @property
    def range_length (self):
        return self.numberOfRanges()

    @property
    def range_vals (self):
        return self._get_range_limits(self.numberOfRanges())

    @property
    def range_counts (self):
        return self._get_range_values(self.numberOfRanges())

    # =====================================================
    # Additional attributes defined in pydsstools.core.grid
    # =====================================================


cdef int save_grid7(long long *ifltab, const char* pathname, float[:,::1] data, object info7):
    cdef:
        zStructSpatialGrid *zsgs=NULL
        # int struct_type
        # pathname
        int struct_ver = VERSION_100
        int grid_type
        int version = 1
        char * data_units
        int data_type
        char * data_source = ""
        int lower_left_x = 0 
        int lower_left_y = 0
        int rows
        int cols
        #float cell_size
        int compression_method
        #int compression_size
        char * crs_name = ""
        int crs_type = 0
        char * crs = ""
        float xcoord_cell0 = 0.0
        float ycoord_cell0 = 0.0
        float nodata = UNDEFINED
        char * tzid = ""
        int  tzoffset = 0
        int is_interval = 0
        int time_stamped = 0
        #int range_length

        # data
        int storage_dtype = GRID_FLOAT
        float max_val,min_val,mean_val
        float * pmin = NULL
        float * pmax = NULL
        float * pmean = NULL
        #float _min,_max,_mean
        int range_length = 0
        int range_counts[20]
        float range_vals[20]
        int status
        int i

    grid_type = info7.grid_type.value

    if grid_type < 0:
        logging.error('Invalid grid type (value = {}). Gridded data was not written'.format(grid_type))
        return -1

    zsgs = zstructSpatialGridNew(pathname)
    rows = int(data.shape[0])
    cols = int(data.shape[1])
    nodata = UNDEFINED

    if info7.shape[0] != rows or info7.shape[1] != cols:
        logging.error('Shape of array data and grid info does not match')
        return -1

    if rows <= 0 or cols <= 0:    
        logging.error('Array data can not be empty.')
        return -1

    data_units = info7.data_units
    data_type = info7.data_type.value
    if data_type < -1:
        logging.error('Invalid grid data type (value = {}). Gridded data was not written'.format(data_type))
        return -1

    compression_method = info7.compression_method.value
    if compression_method == PRECIP_2_BYTE or compression_method <0: # for enum.invalid = -9999
        logging.info('Incompatible compression method (code = {}). ZLIB method used.'.format(compression_method))
        compression_method = ZLIB_COMPRESSION

    lower_left_x = info7.lower_left_cell[0]
    lower_left_y = info7.lower_left_cell[1]
    max_val = info7.max_val
    min_val = info7.min_val
    mean_val = info7.mean_val
    pmax = &max_val
    pmin = &min_val
    pmean = &mean_val
    range_length = len(info7.range_vals)
    for i in range(range_length):
        range_vals[i] = <float>(info7.range_vals[i])
        range_counts[i] = <int>(info7.range_counts[i])

    if grid_type == 410 or grid_type == 421:
        # Hrap
        data_source = info7.data_source

    elif grid_type == 420 or grid_type == 421:
        # Albers
        # This probably makes no difference other than something is written in file
        # DSSVue sees Albers and shows the SHG info
        crs_name = 'Albers'
        crs = SHG_WKT # TODO make custom SHG using input parameters
        #coords_cell0 is default 0,0 above which applies to Albers

    elif grid_type == 430 or grid_type == 431:
        # Spec
        crs_name = info7.crs_name
        crs = info7.crs 
        _nodata = info7.nodata
        tzid = info7.tzid
        tzoffset = info7.tzoffset
        xcoord_cell0 = info7.coords_cell0[0]
        ycoord_cell0 = info7.coords_cell0[1]
        is_interval = int(info7.is_interval)
        time_stamped = int(info7.time_stamped)

    # C structure assignment below
    zsgs[0].pathname  = pathname
    zsgs[0]._structVersion  = struct_ver
    zsgs[0]._type  = grid_type
    # In HEC-DSS 6, I think this is 2 for Specified Grid and not specified for other types
    # HEC-DSS 7 probably updates this value while writing to file
    zsgs[0]._version  = version  
    zsgs[0]._dataUnits  = data_units
    zsgs[0]._dataType  = data_type
    zsgs[0]._dataSource  = data_source
    zsgs[0]._lowerLeftCellX  = lower_left_x
    zsgs[0]._lowerLeftCellY  = lower_left_y
    zsgs[0]._numberOfCellsX  = cols
    zsgs[0]._numberOfCellsY  = rows
    zsgs[0]._cellSize  = <float>info7.cell_size
    zsgs[0]._compressionMethod  = compression_method
    # In zStructTransfer, compression parameters are in
    # member value2Number and values2. Both are set to zero with comment saying - for future use
    # Thus, the compression parameters can be returned as zero (e.g., converting to DSS6) without reading the actual values
    zsgs[0]._compressionParameters  = NULL
    zsgs[0]._srsName  = crs_name
    zsgs[0]._srsDefinitionType  = crs_type
    zsgs[0]._srsDefinition  = crs
    zsgs[0]._xCoordOfGridCellZero  = xcoord_cell0
    zsgs[0]._yCoordOfGridCellZero  = ycoord_cell0
    zsgs[0]._nullValue  = nodata
    zsgs[0]._timeZoneID  = tzid
    zsgs[0]._timeZoneRawOffset  = tzoffset
    zsgs[0]._isInterval  = is_interval
    zsgs[0]._isTimeStamped  = time_stamped
    zsgs[0]._numberOfRanges  = range_length
    zsgs[0]._storageDataType  = storage_dtype
    zsgs[0]._maxDataValue  = <void *>pmax
    zsgs[0]._minDataValue  = <void *>pmin
    zsgs[0]._meanDataValue  = <void *>pmean
    zsgs[0]._rangeLimitTable  = <void *>range_vals
    zsgs[0]._numberEqualOrExceedingRangeLimit  = <int *>range_counts
    zsgs[0]._data  = <void *>&data[0,0]

    status = zspatialGridStore(ifltab,zsgs)
    return status 

cdef int save_grid0(long long *ifltab, const char* pathname, float[:,::1] data, object gridinfo):
    cdef:
        int rows = 0
        int cols = 0
        int path_len = 0
        int comp_method
        int data_size = 0
        int data_size_bytes = 0
        void * comp_buffer = NULL
        int16_t[::1] _comp_buffer        #for RLE compression
        int comp_buffer_bytes = 0
        int32_t[::1] _comp_buffer_bytes  #for RLE compression 
        int comp_buffer_len = 0
        int comp_status
        int[::1] info_flat
        int info_len 
        int grid_type
        float base
        float factor
        float min_val
        float max_val
        int zero = 0
        int plan = 0
        int dummy_header[1]
        int status[1]
        int exists[1] 
        int one_hour_in_milli = 1000*60*60
        int diff

    rows,cols = gridinfo.rows, gridinfo.cols

    if rows != data.shape[0] or cols != data.shape[1]:
        logging.error('Grid data rows and columns mismatch between data array and gridinfo',exc_info=False)
        logging.info('Grid data not written to dss file')
        return -1

    data_size = rows * cols
    data_size_bytes = rows * cols * data.itemsize
    path_len = strlen(pathname)
    grid_type = gridinfo.grid_type
    comp_method = gridinfo.compression_method
    base = gridinfo.compression_base
    factor = gridinfo.compression_factor
    max_val = gridinfo.max_val
    min_val = gridinfo.min_val

    # 0 Undefined
    # 1 No Compression
    # 26  Zlib Deflate
    # 101001 PRECIP_2_BYTE      

    # check for special situation
    if comp_method == UNDEFINED_COMPRESSION_METHOD: # = 0
        diff = (gridinfo.etime - gridinfo.etime)*60*1000
        logging.debug('Grid time window interval in milli seconds = {} is compared with one-hour-mill - {}'.format(diff,one_hour_in_milli))
        if gridinfo.version() == 1 and one_hour_in_milli == diff and gridinfo.data_type == 1: # per-cum data type
            logging.info('Undefined compression was changed to HEC-RLE compression')
            comp_method = PRECIP_2_BYTE
        else:        
            logging.info('Undefined compression was changed to ZLIB compression')
            comp_method = ZLIB_COMPRESSION

    # compress data
    if comp_method == ZLIB_COMPRESSION:
        # Case for undefined and zlib compression
        logging.info('Apply zlib compression to grid data before writing to dss file.')
        #gridinfo.compression_method = 26
        comp_buffer_bytes = compress_zlib(<void*>&data[0,0], data_size_bytes, &comp_buffer)
        comp_buffer_len = <int>((comp_buffer_bytes + 4 - 1)/4.0) # padding
        gridinfo.compression_size = comp_buffer_bytes
        gridinfo.compression_factor = 0 # hard coding for now
        gridinfo.compression_base = 0 # hard coding for now
        logging.info("Size of grid data: {} bytes".format(data_size_bytes))
        logging.info("Size of compressed data: {} bytes".format(comp_buffer_bytes))
        logging.info("Length of compressed data: {}".format(comp_buffer_len))

    elif comp_method == PRECIP_2_BYTE:
        # Case of PRECIP_2_BYTES
        logging.warn('Applying HEC-Style RLE compression to grid data before writing to dss file.')
        # update the parameters first
        if base == NODATA_FLOAT and factor == NODATA_FLOAT:
            base = 100.0
            factor = 0.0
            if min_val < base:
                base = floor(min_val)
                diff = <int>((max_val - base)*factor)
                if diff > 32768: # max number for 15 bits
                    base = ceil(32767.0/(max_val - min_val))

        _comp_buffer = np.empty(data_size,dtype=np.int16) # output buffer for compression, which will be later type-casted to void *
        _comp_buffer_bytes = np.empty(1,dtype=np.int32)   # true size of the compressed data in bytes, unpadded
        # convert 2D buffer (C-contiguous) to 1D buffer (C-contiguous) that hec_compress expects
        comp_status = hec_compress(<f32[:data_size]>&data[0,0],data_size,factor,base,_comp_buffer, _comp_buffer_bytes)

        if comp_status != 0:
            logging.error('There was error compressing the grid data using HEC-Style RLE compression. Grid version 6 data was not written.')
            return -1

        comp_buffer = <void*>&_comp_buffer[0] # zlib uses void* buffer, so doing this for clean code without extra variables
        comp_buffer_bytes = _comp_buffer_bytes[0]  
        comp_buffer_len = <int>((comp_buffer_bytes + 4 - 1)/4.0) # padding
        gridinfo.compression_size = comp_buffer_bytes
        gridinfo.compression_base = base
        gridinfo.compression_factor = factor
        logging.info("Size of grid data: {} bytes".format(data_size_bytes))
        logging.info("Size of compressed data: {} bytes".format(comp_buffer_bytes))
        logging.info("Length of compressed data: {}".format(comp_buffer_len))

    elif comp_method == NO_COMPRESSION:
        # Case of no compression
        logging.info('No compression to grid data before writing to dss file.')
        comp_buffer = <void*>&data[0,0]
        comp_buffer_bytes = data_size_bytes
        comp_buffer_len = rows * cols            
        gridinfo.compression_size = comp_buffer_bytes
        gridinfo.compression_factor = 0 # hard coding for now
        gridinfo.compression_base = 0 # hard coding for now

    else:    
        logging.info('Incompatible compression method provided. Grid version 6 data was not written.')
        return -1

    # get flatten (numpy int32 gridinfo buffer) from profile
    # grid info/meta data as int buffer
    logging.debug('Final gridinfo header in string format to be written to dss file:\n{}'.format(gridinfo.to_dict()))
    info_flat = gridinfo.to_int_array()
    info_len = info_flat.size
    logging.debug('Length of final gridinfo header as integer buffer:\n{}'.format(info_len))
    logging.debug('Final gridinfo header as integer buffer:\n{}'.format(np.asarray(info_flat)))

    # Write to dss file
    # zwritex is C API
    # zwritex_ is fortran API. Using this may have required the string as Hollerith representation.   
    # not sure why &grid_type is needed in zwritex
    zwritex(ifltab,
            pathname, &path_len,
            &info_flat[0],&info_len,
            dummy_header,&zero,
            dummy_header,&zero,
            <int *>comp_buffer,&comp_buffer_len,
            &grid_type,
            &plan,
            status,
            exists,
            )

    logging.info("Grid data written to file with status code = {}".format(status[0]))
    return status[0]

cdef int get_gridver_from_path(long long *ifltab, const char* pathname):
    cdef:
        int version = -1
        int status = 0

    status = zspatialGridRetrieveVersion(ifltab,pathname,&version)    
    if status !=0:
        return -1
    # 100 = DSS7 
    # 0 = DSS6
    return version    

#cdef np.ndarray read_gridv6(long long *ifltab, const char* pathname, int[::1] info6, bint retrieve_data):
cdef int get_gridtype_from_path(long long *ifltab, const char* pathname):
    cdef:
        zStructRecordSize *srs_ptr = NULL
        int grid_type = 0
        int exists = 0

    srs_ptr = zstructRecordSizeNew(pathname)
    if srs_ptr == NULL:
        return -1

    exists = zgetRecordSize(ifltab,srs_ptr)
    if exists != 0:
        return -1

    grid_type = srs_ptr.dataType
    # TODO: verify this won't cause any memory leakage
    zstructFree(srs_ptr)
    return grid_type

cdef int get_grid_datalen_from_path(long long *ifltab, const char* pathname):
    cdef:
        zStructRecordSize *srs_ptr = NULL
        int comp_len = 0
        int exists = 0

    srs_ptr = zstructRecordSizeNew(pathname)
    if srs_ptr == NULL:
        return -1

    exists = zgetRecordSize(ifltab,srs_ptr)
    if exists != 0:
        return -1

    comp_len = srs_ptr.values1Number
    # TODO: verify this won't cause any memory leakage
    zstructFree(srs_ptr)
    return comp_len

cdef np.ndarray read_grid0(long long *ifltab, const char *pathname, object ginfo6, bint retrieve_data):
    cdef:
        int grid_type
        int flat_size = 0
        np.ndarray info_flat
        int[::1] info_flat_mv
        int comp_data_len
        np.ndarray comp_data
        int[::1] comp_data_mv
        int16_t[::1] comp_data16
        int16_t[::1] comp_data16_mv
        int comp_method
        float comp_base
        float comp_factor
        np.ndarray out_data
        f32[::1] out_data_mv
        int32_t[::1] out_size_mv
        int data_size
        int rows
        int cols
        float nodata
        float min_val
        float max_val
        int i
        int dummy_header[1]
        int zero = 0
        int plan = 0
        int found = 0
        int status
        int exists

    grid_type = ginfo6.grid_type
    comp_data_len = get_grid_datalen_from_path(ifltab,pathname)

    #flat_size = ginfo.info_fsize
    info_flat = ginfo6.to_int_array()
    info_flat_mv = info_flat

    #comp_buffer = <int*>malloc(comp_data_len * sizeof(int))
    #if comp_buffer == NULL:
    #    raise MemoryError()
    comp_data = np.empty(comp_data_len,dtype=np.int32)
    comp_data_mv = comp_data

    # fill grid meta into info_flat,get compressed data
    zreadx(ifltab,
           pathname,
           &info_flat_mv[0], &flat_size, &flat_size,
           dummy_header, &zero, dummy_header,
           dummy_header, &zero, dummy_header,
           &comp_data_mv[0], &comp_data_len, &comp_data_len,
           &plan,
           &found
    )
    if found == 0:
        return None

    ginfo6.update_from_int_array(info_flat)

    if not retrieve_data:
        return info_flat

    if retrieve_data:
        grid_type = ginfo6.grid_type
        rows = ginfo6.rows
        cols = ginfo6.cols
        data_size = rows * cols
        comp_method = ginfo6.compression_method
        comp_base = ginfo6.compression_base
        comp_factor = ginfo6.compression_factor
        min_val = ginfo6.min_val
        max_val = ginfo6.max_val
        logging.debug('rows={},cols={},comp method = {},comp data len = {}'.format(rows,cols,comp_method,comp_data_len))

        if data_size == 0:
            return None

        if comp_method == NO_COMPRESSION:
            out_data = np.astype(comp_data,dtype=np.float32)

        elif comp_method == ZLIB_COMPRESSION:
            #data = <float*>malloc(data_size*sizeof(float))
            #if data == NULL:
            #    return None    
            out_data = np.empty(data_size,dtype=np.float32)
            out_data_mv = out_data


            # int uncompress_zlib(const void* buffer, int size, void* data, int dataSize)
            status = uncompress_zlib(<void*>&comp_data_mv[0],comp_data_len,
                                    <void*>&out_data_mv[0],data_size
                                    )
            if status != 0:
                 return

            if grid_type == 430:
                nodata = ginfo6.nodata
                out_data[out_data == nodata] = UNDEFINED_FLOAT

            else:
                out_data[(out_data < min_val) | (out_data > max_val)] = UNDEFINED_FLOAT

        elif comp_method == PRECIP_2_BYTE:
            #comp_data16_mv = <int16_t[:comp_data_len*2]><int16_t *>&comp_data_mv[0]
            # OverflowError: character argument not in range(0x110000)
            # use np.view instead of raw pointer casting
            comp_data16 = comp_data.view(np.int16)
            comp_data16_mv = comp_data16
            out_data = np.empty(data_size,dtype=np.float32)
            out_data_mv = out_data
            out_size = np.empty(1,dtype=np.int32)
            out_size_mv = out_size
            # TODO: Review needed
            # assuming int is int32. What if int is 16 or 64? In this case comp_data_len*2 fails
            status = hec_uncompress(comp_data16_mv,comp_data_len*2,
                                    comp_factor,comp_base,
                                    out_data_mv,
                                    out_size_mv,
                                    UNDEFINED_FLOAT)
            if status !=0:
                logging.error('Problem with decoding HEC-style RLE compressed data for grid')
                return
            # It seems the following is unnecessary
            #if grid_type == 430:
            #    nodata = ginfo6.nodata
            #    # TODO: gridinfo will still show nodata value different than UNDEFINED_FLOAT
            #    out_data[out_data == nodata] = UNDEFINED_FLOAT
            #
            #else:
            #    out_data[(out_data < min_val) | (out_data > max_val)] = UNDEFINED_FLOAT

        else:
            out_data =  None
        
        if not out_data is None:
            out_data = np.ma.masked_values(out_data,UNDEFINED_FLOAT)

        return out_data





