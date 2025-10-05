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
            logging.debug("Freeing timeseries struct")
            zstructFree(self.tss)

    @property
    def count(self):
        """ 
        Returns
        ------- 
            # Total number of records/data in the time-series.
            # None when the time-series is empty or invalid. 
        """
        cdef int num = 0
        if self.tss:
            num = self.tss[0].numberValues
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
            int num = self.count
            int interval
            int granularity
            np.ndarray values
            HecTime htime
            int i,x
            view.array mview = view.array(shape=(num,), 
                                            itemsize=sizeof(int),format='i',
                                            allocate_buffer=False)

        if self.tss:
            interval = self.interval #seconds
            if interval <= 0:
                granularity = self.granularity
                mview.data = <char *>(self.tss[0].times)
                values = np.asarray(mview)
                for i in range(num):
                    x = values[i]
                    htime = HecTime(x,granularity=granularity,julian_base=self.tss[0].julianBaseDate)
                    yield htime

            else:
                # HecTime
                htime = self.start_time.clone()
                for i in range(num):
                    yield htime
                    htime = htime.clone()
                    htime.add_time(interval,1) 


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
        cdef int num
        if self.tss:
            num = self.count
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
    def data_type(self):
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
    def data_units(self):
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
    def start_time(self):
        if self.tss:
            #return " ".join(_getDateAndTime(self.tss[0].startTimeSeconds, 1, self.tss[0].startJulianDate))
            #return "{} {}".format(HecTime._datetime_from_value(self.tss[0].startTimeSeconds,1,self.tss[0].startJulianDate))
            htime = HecTime(self.tss[0].startTimeSeconds, granularity = 1, julian_base = self.tss[0].startJulianDate, midnight_as_2400 = False)
            return htime
            
    @property
    def end_time(self):
        if self.tss:
            #return " ".join(_getDateAndTime(self.tss[0].endTimeSeconds, 1, self.tss[0].endJulianDate))
            #return "{} {}".format(HecTime._datetime_from_value(self.tss[0].endTimeSeconds,1,self.tss[0].endJulianDate))
            htime = HecTime(self.tss[0].endTimeSeconds, granularity = 1, julian_base = self.tss[0].endJulianDate, midnight_as_2400 = True)
            return htime

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
    def tzid(self):
        timezone = ''        
        if self.tss:
            if self.tss[0].timeZoneName:
                timezone = self.tss[0].timeZoneName
        return timezone        

    @property
    def julian(self):
        if self.interval <= 0:
            return self.tss[0].julianBaseDate
        
        else:
            return (self.tss[0].startJulianDate,self.tss[0].endJulianDate)


cdef class TimeSeriesContainer:
    cdef:
        str _pathname
        int _count
        int _interval
        int _granularity
        np.ndarray _values
        np.ndarray _times
        HecTime _start_time
        HecTime _julian_base
        str _data_units
        str _data_type
        object _tzid

        float[:] _values_mv
        float* _values_ptr
        int[:] _times_mv
        int* _times_ptr
        char *_ctzid

    def __init__(self,pathname,count,interval,**kwargs):

        self.pathname = pathname
        self.count = count
        self.interval = interval
        #self.start_time = kwargs.pop("start_time","31DEC1899:0000")    
        self.data_units = kwargs.pop("data_units","")    
        self.data_type = kwargs.pop("data_type","")    
        self.tzid = kwargs.pop("tzid","")    
        self.julian_base = kwargs.pop("julian_base",HecTime("31DEC1899:0000",granularity=60))    
        #self._timezone_bytes = _tzid.encode('ascii')
        #self.timeZoneName = PyBytes_AS_STRING(self._timezone_bytes)
        #self._startDateBase=''

    @property
    def pathname(self):
        return self._pathname    

    @pathname.setter
    def pathname(self,value):
        if isinstance(value, str):
            self._pathname = value   
        elif isinstance(value, DssPathName):
            self._pathname = value.text()
        else:
            raise ValueError(f'Expected string or DssPathname for pathname, got {type(value).__name__}')        

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self,count):
        if not isinstance(count,int):
            raise TypeError(f"Expect integer value for length of values, got {type(count).__name__}")

        if count <=0:
            raise ValueError(f"Length of values cannot be zero or less")
        
        self._count = count

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self,interval):
        if not isinstance(interval,int):
            raise TypeError(f"Expect integer value for interval, got {type(interval).__name__}")
        self._interval = interval

    @property
    def start_time(self):
        if self.count > 0:
            return self._start_time

    @start_time.setter
    def start_time(self,datetime):
        if self.count > 0:
            if isinstance(datetime,str):
                self._start_time = HecTime(datetime,60,midnight_as_2400=False)
            elif isinstance(datetime,HecTime):
                self._start_time = datetime
            else:
                raise TypeError(f"start time for regular timeseries must be HecTime or date string, got {type(datetime).__name__}") 

    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self,values):
        if values is not None:
            if isinstance(values,array.array):
                _values = np.asarray(values,np.float32)
                
            elif isinstance(values,np.ndarray):
                _values = np.ascontiguousarray(values,dtype=np.float32)

            elif isinstance(values,(list,tuple)):
                _values = np.array(values,np.float32)

            else:
                raise "Invalid value"  

            assert _values.ndim == 1, f"value should be 1 dimension array type, got dimension of {_values.ndim}"
            assert len(_values) == self.count, "Length of value does not match the count"

            self._values = _values
            self._values_mv = self._values    
            self._values_ptr = &self._values_mv[0]    

    @property
    def times(self):
        return self._times
    
    @times.setter
    def times(self,values):
        if values is not None and self.interval <= 0:
            if not isinstance(values,(np.ndarray,array.array,list,tuple)):
                raise ValueError(f"Expect array,ndarray,array,list or tupe of HecTime or integer time value, got {type(values).__name__}")    

            if isinstance(values[0],HecTime):
                _times = np.array([x.value() for x in values], dtype=np.int32)

            elif isinstance(values[0],datetime):
                _times = np.array([HecTime(x,granularity=60).value() for x in values], dtype=np.int32)

            elif isinstance(values,array.array):
                _times = np.asarray(values,np.int32)
                
            elif isinstance(values,np.ndarray):
                assert values.ndim == 1, f"times should be 1 dimension np.array type, got dimension of {values.ndim}"
                _times = np.ascontiguousarray(values,dtype=np.int32)

            elif isinstance(values,(list,tuple)):
                _times = np.array(values,np.int32)

            else:
                raise "Invalid times"  

            assert _times.ndim == 1, f"times should be 1 dimension array type, got dimension of {_times.ndim}"
            assert len(_times) == self.count, "Length of times does not match the count"

            self._times = _times
            self._times_mv = self._times    

    @property
    def data_units(self):
        return self._data_units

    @data_units.setter
    def data_units(self,data):
        self._data_units = data

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self,data):
        self._data_type = data

    @property
    def tzid(self):
        return self._tzid.decode("ascii")

    @tzid.setter
    def tzid(self,data):
        self._tzid = data.encode("ascii")
        self._ctzid = PyBytes_AS_STRING(self._tzid)

    @property
    def julian_base(self):
        if self.interval <=0:
            return self._julian_base.date()

    @julian_base.setter
    def julian_base(self,date):
        if self.interval <=0:
            if isinstance(date,str):
                self._julian_base = HecTime(date,60)
            elif isinstance(date,HecTime):
                self._julian_base = date
            else:
                raise TypeError(f"Julian base date for irregular timeseries must be HecTime or date string, got {type(date).__name__}") 

    cdef TimeSeriesStruct create_tss(self):
        cdef:
            zStructTimeSeries *tss=NULL
            TimeSeriesStruct ts_st
            char *pathname = self._pathname
            float *val_ptr
            int count = self._count
            char *data_units = self._data_units
            char *data_type = self._data_type
            int interval = self._interval
            int *time_ptr
            int granularity
            char *start_date
            char *start_time
            char *julian_base

        if self._values is None:
            raise ValueError("Timeseries values is not defined")

        val_ptr = self._values_ptr

        if interval > 0:
            # Regular Timeseries
            _start_date = self.start_time.date()
            _start_time = self.start_time.time()
            start_date = _start_date
            start_time = _start_time
            tss = zstructTsNewRegFloats(pathname,val_ptr, count,
                                        start_date, start_time,
                                        data_units,data_type)

        else:
            # Irregular Timeseries
            if self._times is None:
                raise ValueError("Irregular timeseries times is not defined")

            time_ptr = <int *>&self._times_mv[0]
            granularity = self._granularity

            julian_base = NULL
            if self._julian_base is HecTime:
                _julian_base = self.julian_base.date()
                julian_base = _julian_base

            tss = zstructTsNewIrregFloats(pathname,val_ptr, count,
                                          time_ptr, granularity,
                                          julian_base,
                                          data_units,data_type)
        if self._tzid:
            tss[0].timeZoneName = self._ctzid

        ts_st = createTSS(tss)
        #logging.debug("length = {}".format(ts_st.count))
        return ts_st  
