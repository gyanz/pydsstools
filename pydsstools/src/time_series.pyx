#cython: c_string_type=str, c_string_encoding=ascii
cdef TimeSeriesStruct createTSS(zStructTimeSeries *tss):
    """Creates time-series struct
    
    Returns
    -------
        # TimeSeriesStruct class

    Usage
    -----
        # Available only in extension scripts
    """
    ts_st = TimeSeriesStruct()
    if tss:
        if tss[0].numberValues>=1:
            ts_st.tss = tss
        else:
            zstructFree(tss)            
            tss=NULL
    return ts_st   


cdef class TimeSeriesStruct:
    """ 
    Python Extension class container for time-series structure retrieved from HEC-DSS file.

    Parameters
    ----------
        # None

    Returns
    -------
        # self

    Usage 
    -----
        # Can only used in the cython extension script 
        # The class instance is not writable in CPython interpretor
        # The member methods or properties return None if time-series s 
        >>> ts_st = TimeSeriesStruct()            
        >>> ts_st.tss = tss # where tss is pointer to HEC-DSS timeseries struct

    """
    cdef:
        zStructTimeSeries *tss

    def __cinit__(self,*arg,**kwargs):
        self.tss=NULL

    cdef int get_number(self):
        cdef int num
        num = self.tss[0].numberValues
        return num 

    def get_times(self,array_length):
        cdef: 
            int length = array_length
            view.array mview = view.array(shape=(length,), 
                                            itemsize=sizeof(int),format='i',
                                            allocate_buffer=False)
        mview.data = <char *>(self.tss[0].times)
        return np.asarray(mview)

    def get_values(self,array_length):
        cdef: 
            int length = array_length
            view.array mview = view.array(shape=(length,), 
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)
        mview.data = <char *>(self.tss[0].floatValues)
        return np.asarray(mview)


    def get_double_values(self,array_length):
        cdef: 
            int length = array_length
            view.array mview = view.array(shape=(length,), 
                                            itemsize=sizeof(double),format='d',
                                            allocate_buffer=False)
        mview.data = <char *>(self.tss[0].doubleValues)
        return np.asarray(mview)

    # No NULL pointer check for above function
    # NULL check with following functions

    def __dealloc__(self):
        if self.tss:
            zstructFree(self.tss)

    @property
    def numberValues(self):
        """ 
        Returns
        ------- 
            # Total number of records/data in the time-series.
            # None when the time-series is empty or invalid. 
        """
        cdef int num
        if self.tss:
            num = self.get_number()
            return num 

    @property
    def times(self):
        """
        Returns memoryview of the underlying C integer array of times.The time
        values are usually minutes since 31 DEC 1899 00:00:00. But it could be
        other time units (i.e. seconds) depending upon the granularity value 
        of the time-series. For minute granularity, granularity value is 60 seconds,
        for second granularity, it is 1, and so on. 

        Returns
        -------
            # Memoryview object of the integer time array
            # None when the time-series is empty or invalid

        Usage
        -----
            # Single element indexing is similar to list object  
            # Range indexing returns memoryview which can be converted to python 
              list using `list` on the memoryview. Note that using list creates
              the copy of the time array.
            # To avoid making copy of the data, numpy.asarray(memoryview of array)
              can be used.
            >>> times = tsc.times
            <MemoryView of 'array' at 0x485b3d0>
            >>> times_0 = times[0]
            55851840
            >>> time_list = list(times)
            >>> time_list
            [55851840, 55853280, ...]
            
        """
        cdef:
            int num
            int interval
            list reg_times
            int i,sec_sum

        if self.tss:
            interval = self.interval
            num = self.get_number()
            if interval <= 0:
                return self.get_times(num).tolist()
            else:
                reg_times = []
                sec_sum = self.tss[0].startTimeSeconds 
                logging.debug('Computing times for regular time-series (granularity = second, startJulianDate = %r ):'%(self.tss[0].startJulianDate))
                for i in np.arange(self.get_number()):
                    reg_times.append(sec_sum)
                    sec_sum = sec_sum + interval 
                return reg_times

    @property
    def pytimes(self):
        cdef:
            list times,datetimes
            int interval,granularity

        if self.tss:
            interval = self.interval
            times = self.times
            if times:
                if interval <= 0:
                    granularity = self.granularity
                    datetimes = [getPyDateTimeFromValue(x,granularity,self.tss[0].julianBaseDate) for x in times]    
                else:
                    datetimes = [getPyDateTimeFromValue(x,1,self.tss[0].startJulianDate) for x in times]
                return datetimes


    @property
    def values(self):
        """
        Returns memoryview of the underlying C float array of values in the 
        time series.
 
        Returns
        -------
            # Memoryview object of the float value array
            # None when the time-series is empty or invalid

        Usage
        -----
            # Single element indexing is similar to list object  
            # Range indexing returns memoryview which can be converted to python 
              list using `list` on the memoryview. Note that using list creates
              the copy of the time array.
            # To avoid making a copy of the data, numpy.asarray(memoryview of array)
              menthod can be used.
        """
        cdef num
        if self.tss:
            num = self.get_number()
            if self.tss[0].floatValues:
                return self.get_values(num)
            elif self.tss[0].doubleValues:
                return self.get_double_values(num)
            else:
                pass

    @property
    def nodata(self):
        cdef:
            np.ndarray values
            np.ndarray result

        values = self.values
        if not values is None:
            if self.tss[0].floatValues:
                check = lambda x : zisMissingFloat(x)==1
            elif self.tss[0].doubleValues:
                check = lambda x : zisMissingDouble(x)==1

            func = np.vectorize(check)
            result = func(values)
            return result

    @property
    def empty(self):
        result = self.nodata
        if not result is None:
            return (~(~result).any())
        return True


    @property
    def type(self):
        """Returns the type of the time-series
        
        Returns
        -------
            # PER-AVER, PER-CUM, INST-VAL or INST-CUM 
            # These are byte string (or ascii encoded) objects

        """
        if self.tss:
            if self.tss[0].type:
                return self.tss[0].type
        return ''

    @property
    def units(self):
        """Returns the unit of values in the time-series
        
        Returns
        -------
            # CFS, FEET, ... etc.  
            # These are byte string (or ascii encoded) objects

        """
        if self.tss:
            if self.tss[0].units:
                return self.tss[0].units
        return ''

    @property
    def pathname(self):
        """Returns the pathname (ascii encoded) of the time-series"""
        if self.tss:
            if self.tss[0].pathname:
                return self.tss[0].pathname
        return ''

    @property
    def pathnameInternal(self):
        if self.tss:
            return
            #return self.tss[0].pathnameInternal

    @property
    def granularity(self):
        """Returns the granularity of time values used in the time-series.
           Granularity value is time in seconds. It is 1 and 60 for second and
           minute granularities respectively.  

        Example
        -------
            # Lets say, a time value is 172800 with a granularity of seconds.
              This means it is 172800/(3600*24) days since 31 DEC 1899 00:00:00,
              which is 2 January 1900 00:00:00  
            # Lets say, another time value is 4320 with a granularity of minutes.
              This would be 3 January 1900 00:00.
    
        """
        if self.tss:
            return self.tss[0].timeGranularitySeconds

    @property
    def startDateTime(self):
        if self.tss:
            return " ".join(_getDateAndTime(self.tss[0].startTimeSeconds, 1, self.tss[0].startJulianDate))
            
    @property
    def endDateTime(self):
        if self.tss:
            return " ".join(_getDateAndTime(self.tss[0].endTimeSeconds, 1, self.tss[0].endJulianDate))

    @property
    def startPyDateTime(self):
        """Returns start date and time of the time-series

        Returns
        -------
            # Python datetime object
    
        """
        if self.tss:
            return getPyDateTimeFromValue(self.tss[0].startTimeSeconds, 1, self.tss[0].startJulianDate)        

    @property
    def endPyDateTime(self):
        """Returns end date and time of the time-series

        Returns
        -------
            # Python datetime object
    
        """
        if self.tss:
            return getPyDateTimeFromValue(self.tss[0].endTimeSeconds, 1, self.tss[0].startJulianDate)        

    @property
    def interval(self):
        if self.tss:
            return self.tss[0].timeIntervalSeconds

    @property
    def dtype(self):
        interval = self.interval
        if interval is None:
            return "Unknown Type"
        elif interval <= 0:
            return "Irregular TimeSeries"
        elif interval > 0:
            return "Regular TimeSeries"
        else:
            return "Undefined"

    @property
    def _julian_base_date(self):
        if self.tss:
            return {'julianBaseDate':self.tss[0].julianBaseDate, 'startJulianDate':self.tss[0].startJulianDate}        

cdef class TimeSeriesContainer:
    cdef:
        public str pathname
        public int interval
        public int granularity
        public int numberValues 
        public object times
        public str startDateTime
        public str units
        public str type
        public str _startDateBase #for overflowing time in irregular time-series TODO
        object _values
        float *floatValues
        double *doubleValues
        float [:] float_mv
        double [:] double_mv
        void *Values
        int [:] int_mv
        int *intTimes

    def __init__(self,**kwargs):
        _pathname = kwargs.get('pathname','')
        _interval = kwargs.get('interval',1) # regular tsc by default
        _granularity = kwargs.get('granularity',60)
        __values = kwargs.get('values',None) 
        _times = kwargs.get('times',None) 
        _units = kwargs.get('units','')
        _type = kwargs.get('type','')
        _startDateTime = kwargs.get('startDateTime','')

        self.pathname =_pathname 
        self.interval = _interval
        self.granularity = _granularity
        self._values =  __values
        self.times =  _times
        self.units = _units
        self.type = _type
        self.startDateTime= _startDateTime
        self._startDateBase=''

    cdef int setFloatValues(self):
        """ Used by setValues member function to set Regular time-series values
        """
        logging.debug("Setting floatValues")
        if isinstance(self._values,array.array):
            if self._values.typecode == 'f':
                self.float_mv = self._values
                self.floatValues=&self.float_mv[0]
            else:
                self.setPyListType('f')

        elif isinstance(self._values,(list,tuple)):
            self.setPyListType('f')

        elif isinstance(self._values,np.ndarray):
            if self._values.dtype==np.float32:
                self.float_mv = self._values
                self.floatValues=&self.float_mv[0]
            else:
                self.float_mv = self._values.astype(np.float32)
                self.floatValues=&self.float_mv[0]

        else:
            raise "Invalid Values"

        self.doubleValues=NULL

    cdef int setDoubleValues(self):
        """ Used by setValues member function to set Irregular time-series values
        """
        logging.debug("Setting doubleValues")
        if isinstance(self._values,array.array):
            if self._values.typecode == 'd':
                self.double_mv = self._values
                self.doubleValues=&self.double_mv[0]
            else:
                self.setPyListType('d')

        elif isinstance(self._values,(list,tuple)):
            self.setPyListType('d')

        elif isinstance(self._values,np.ndarray):
            if self._values.dtype==np.float64:
                self.double_mv = self._values
                self.doubleValues=&self.double_mv[0]
            else:
                self.double_mv = self._values.astype(np.float64)
                self.doubleValues=&self.double_mv[0]

        else:
            raise "Invalid Values"

        self.floatValues=NULL

    cdef int setPyListType(self,type_code='f'):
        if type_code == 'f':
            self.float_mv = array.array(type_code,self._values)
            self.floatValues=&self.float_mv[0]
        elif type_code == 'd':
            self.double_mv = array.array(type_code,self._values)
            self.doubleValues=&self.double_mv[0]
        else:
            pass
        
    cdef int setTimePtr(self) except *:
        """Sets pointer to time array, only needed for irregular time-series
        """
        logging.debug("Setting times")
        if isinstance(self.times,array.array):
            if self.times.typecode in ('i',):
                self.int_mv = self.times
                self.intTimes=&self.int_mv[0]
            else:
                logging.error('Typecode error: Time array typecode must be i') 
                raise Exception("Typecode error: Time array typecode must be i") 

        elif isinstance(self.times,(list,tuple)):
            self.int_mv = np.array(self.times,dtype=np.int32) #array.array('l',self.times)
            self.intTimes=&self.int_mv[0]

        elif isinstance(self.times,np.ndarray):
            if self.times.dtype==np.int32:
                self.int_mv = self.times
                self.intTimes=&self.int_mv[0]
            else:
                self.int_mv = self.times.astype(np.int32)
                self.intTimes=&self.int_mv[0]

        else:
            logging.error('Value error: Time array is invalid') 
            raise Exception("Invalid Time Values/Type")
    
    cpdef int setValues(self):
        """Extension function to set correct pointer type to the user entered values
           data
        """
        assert self.numberValues > 0, "Number of values should be > 0"
        assert self.numberValues == len(self._values), "Number of values not equal"
        if self.interval <= 0:
            self.setDoubleValues()
            self.Values = self.doubleValues
            assert self.numberValues == len(self.times), "Number of values not equal to number of times"
            self.setTimePtr()
        else:
            self.setFloatValues()
            self.Values = self.floatValues

    @property
    def values(self):
        """Return values inputted by the user
        """
        return self._values

    @values.setter
    def values(self,values):
        """Allows user to set time-series values
        """
        self._values = values

cdef TimeSeriesStruct createNewTimeSeries(TimeSeriesContainer tsc):
    cdef:
        zStructTimeSeries *tss=NULL
        TimeSeriesStruct ts_st
        char *pathname = tsc.pathname
        void *value_pointer = <void *>tsc.Values
        int numberValues = tsc.numberValues
        char *units = tsc.units
        char *_type = tsc.type
        int interval = tsc.interval
        int *time_pointer
        int granularity
        char *startDate
        char *startTime
        char *startDateBase=NULL

    if not interval <= 0:
        startDateTime = HecTime(tsc.startDateTime)
        _startDate = startDateTime.dateString()
        startDate = _startDate 
        _startTime = startDateTime.timeString()
        startTime = _startTime 
        logging.debug("{},{}".format(startDate,startTime))
        tss = zstructTsNewRegFloats(pathname,<float *>value_pointer,
                    numberValues,startDate, startTime,units,_type)
    else:
        time_pointer = <int *>tsc.intTimes
        granularity = tsc.granularity
        #if not (granularity == 1 or granularity == 60):
        #raise GranularityException(granularity,'Granularity of irregular timeseries must be either 1 or 60 seconds')
        if tsc._startDateBase:
            startDateBase = <char *>tsc._startDateBase
        tss = zstructTsNewIrregDoubles(pathname,<double *>value_pointer,
                    numberValues,time_pointer, granularity,startDateBase,units,_type)

    if not tss:
        logging.debug("Empty time-series struct created")

    ts_st = createTSS(tss)
    logging.debug("length = {}".format(ts_st.numberValues))
    return ts_st  

