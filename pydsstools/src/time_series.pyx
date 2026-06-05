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
            logger.debug("Freeing timeseries struct")
            zstructFree(self.tss)

    @property
    def vdi(self):
        """Return :class:`VerticalDatumInfo` extracted from the user header, or
        ``None`` if no VDI is present or the user header was not read
        (``boolRetrieveVdi=False`` on the read call)."""
        from pydsstools.core.vdi import VerticalDatumInfo
        cdef:
            verticalDatumInfo *vdi = NULL
            double undef = UNDEFINED_VERTICAL_DATUM_VALUE
        if not (self.tss and
                self.tss[0].userHeaderNumber > 0 and
                self.tss[0].userHeader != NULL):
            return None
        vdi = extractVerticalDatumInfoFromUserHeader(
            self.tss[0].userHeader, self.tss[0].userHeaderNumber)
        if vdi == NULL:
            return None
        result = VerticalDatumInfo(
            native_datum=(<bytes>vdi[0].nativeDatum).decode("ascii", "replace").rstrip('\x00').strip(),
            unit=(<bytes>vdi[0].unit).decode("ascii", "replace").rstrip('\x00').strip(),
            offset_to_navd88=(None if vdi[0].offsetToNavd88 == undef
                              else vdi[0].offsetToNavd88),
            navd88_is_estimate=bool(vdi[0].offsetToNavd88IsEstimate),
            offset_to_ngvd29=(None if vdi[0].offsetToNgvd29 == undef
                              else vdi[0].offsetToNgvd29),
            ngvd29_is_estimate=bool(vdi[0].offsetToNgvd29IsEstimate),
        )
        free(vdi)
        return result

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
    def quality_flags(self):
        """
        Returns quality array as a 2-D numpy int32 array of shape
        (numberValues, qualityElementSize), or None if not retrieved.
        """
        cdef:
            int n
            int elem_size
            view.array mview
        if self.tss and self.tss[0].qualityElementSize > 0 and self.tss[0].quality != NULL:
            n = self.tss[0].numberValues
            elem_size = self.tss[0].qualityElementSize
            mview = view.array(shape=(n * elem_size,),
                               itemsize=sizeof(int), format='i',
                               allocate_buffer=False)
            mview.data = <char *>self.tss[0].quality
            return np.asarray(mview).reshape(n, elem_size)
        return None

    @property
    def integer_notes(self):
        """
        Returns fixed-length integer notes as a 2-D numpy int32 array of shape
        (numberValues, inoteElementSize), or None if not retrieved.
        Mutually exclusive with text_notes.
        """
        cdef:
            int n
            int elem_size
            view.array mview
        if self.tss and self.tss[0].inoteElementSize > 0 and self.tss[0].inotes != NULL:
            n = self.tss[0].numberValues
            elem_size = self.tss[0].inoteElementSize
            mview = view.array(shape=(n * elem_size,),
                               itemsize=sizeof(int), format='i',
                               allocate_buffer=False)
            mview.data = <char *>self.tss[0].inotes
            return np.asarray(mview).reshape(n, elem_size)
        return None

    @property
    def text_notes(self):
        """
        Returns variable-length character notes as a list of str, one per value,
        or None if not retrieved.  Mutually exclusive with integer_notes.
        Empty notes are preserved at their index.
        """
        cdef:
            int total
            int n
            const unsigned char *ptr
        if self.tss and self.tss[0].cnotesLengthTotal > 0 and self.tss[0].cnotes != NULL:
            total = self.tss[0].cnotesLengthTotal
            n = self.tss[0].numberValues
            ptr = <const unsigned char *>self.tss[0].cnotes
            raw = ptr[:total]   # bytes — cast avoids c_string_type=str auto-coercion
            # take exactly numberValues items; trailing sentinel \0 produces a spurious
            # empty string at end of split which is excluded by the [:n] slice
            return [s.decode('ascii') for s in raw.split(b'\0')[:n]]
        return None

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

        # quality and notes
        np.ndarray _quality_flags
        int _quality_elem_size
        int[:] _quality_mv
        int* _quality_ptr

        np.ndarray _integer_notes
        int _inote_elem_size
        int[:] _inotes_mv
        int* _inotes_ptr

        bytes _text_notes_buf
        int _cnotes_length

        object _vdi  # VerticalDatumInfo or None

    def __init__(self,pathname,count,interval,**kwargs):
        self.pathname = pathname
        self.count = count
        self.interval = interval
        self.data_units = kwargs.pop("data_units","")    
        self.data_type = kwargs.pop("data_type","")    
        self.tzid = kwargs.pop("tzid","")    
        self.julian_base = kwargs.pop("julian_base",HecTime("31DEC1899:0000",granularity=60))    
        self.values = kwargs.pop("values",None)
        self.times = kwargs.pop("times",None)
        self.quality_flags = kwargs.pop("quality_flags", None)
        self.integer_notes = kwargs.pop("integer_notes", None)
        self.text_notes    = kwargs.pop("text_notes", None)
        self.vdi = kwargs.pop("vdi", None)
        start_time = kwargs.pop("start_time",None)
        if start_time is not None:
            self.start_time = start_time
        elif interval > 0 and (self.times is not None and len(self.times) > 0):
            start_time = self.times[0]
            self.start_time = start_time    


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
        if self.interval > 0:
            return self._start_time

    @start_time.setter
    def start_time(self,date_time):
        if self.interval > 0:
            if isinstance(date_time,(str,datetime)):
                self._start_time = HecTime(date_time,60,midnight_as_2400=False)
            elif isinstance(date_time,HecTime):
                self._start_time = date_time
            else:
                raise TypeError(f"start time for regular timeseries must be HecTime or date string, got {type(date_time).__name__}") 

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

            elif isinstance(values[0],str):
                _times = np.array([HecTime(x,granularity=60).value() for x in values], dtype=np.int32)

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

            if not np.all(np.diff(_times)>= 0):
                raise ValueError("Irregular timeseries does not have ascending times.")

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
            if isinstance(date,(str,datetime)):
                self._julian_base = HecTime(date,60)
            elif isinstance(date,HecTime):
                self._julian_base = date
            else:
                raise TypeError(f"Julian base date for irregular timeseries must be HecTime or date string, got {type(date).__name__}") 

    @property
    def quality_flags(self):
        """
        Quality flags array for the time series values.

        Each value in the time series can have one or more associated quality integers.
        The number of integers per value is the element size (second dimension).

        Bit layout of a single 32-bit quality integer
        -----------------------------------------------

        In Python, the ``0b`` prefix denotes a binary integer literal — the digits
        following ``0b`` are individual bits (0 or 1), read from left (most significant)
        to right (least significant). Each bit position maps to a power of 2, with bit 1
        being the least significant (rightmost) bit::

            bit position:  ...  8    7    6    5    4    3    2    1
            power of 2:    ...  128  64   32   16   8    4    2    1

        The 32 bits are grouped into fields that behave differently from one another:

        **Bit 1 — Screened (single on/off flag)**
            Must be set (= 1) before any other bit in the integer is meaningful.
            An unscreened value (bit 1 = 0) should have all other bits set to 0.

            ``SCREENED = 1 << 0  # = 1``

        **Bits 2-5 — Validity (mutually exclusive, set exactly one)**
            Encodes the QA verdict for the value. Only one of the four bits may be
            set at a time because a value cannot simultaneously be Okay and Missing::

                OKAY         = 1 << 1  # bit 2 = 2
                MISSING      = 1 << 2  # bit 3 = 4
                QUESTIONABLE = 1 << 3  # bit 4 = 8
                REJECT       = 1 << 4  # bit 5 = 16

        **Bits 6-7 — Current data range (2-bit encoded number, value 0-3)**
            These two bits together represent a single integer (0 to 3), not two
            independent flags. Extract with a right-shift and mask::

                range_value = (flag >> 5) & 0b11   # shift 5, keep 2 bits

            To set range = 2: ``2 << 5  # = 64``

        **Bit 8 — Value differs from original (single on/off flag)**
            Set when the stored value has been modified from its original measurement.

            ``DIFFERS_FROM_ORIGINAL = 1 << 7  # = 128``

        **Bits 9-11 — Revision cause (3-bit encoded number, value 0-7)**
            Three bits encoding why the value was revised (0 = not revised). Extract::

                cause = (flag >> 8) & 0b111   # shift 8, keep 3 bits

            To set cause = 3: ``3 << 8  # = 768``

        **Bits 12-15 — Replacement method (4-bit encoded number, value 0-15)**
            Four bits encoding how a missing or rejected value was replaced. Extract::

                method = (flag >> 11) & 0b1111   # shift 11, keep 4 bits

            To set method = 5: ``5 << 11  # = 10240``

        **Bits 16-26 — Test failure indicators (independent flags, any combination)**
            Each bit represents a separate QA test. Multiple tests can fail
            simultaneously, so any combination of these bits may be set::

                TEST_A = 1 << 15  # bit 16 = 32768
                TEST_B = 1 << 16  # bit 17 = 65536
                # ... up to bit 26

        **Bit 32 — Protect from automatic modification (single on/off flag)**
            Prevents automated processes from overwriting this value.

            ``PROTECT = 1 << 31  # = 2147483648``

        Composing a complete flag with bitwise OR::

            SCREENED     = 1 << 0
            OKAY         = 1 << 1
            MISSING      = 1 << 2
            QUESTIONABLE = 1 << 3

            # screened and valid
            SCREENED_OKAY         = SCREENED | OKAY           # 3
            # screened, missing, revised by interpolation (method=2), cause=1
            SCREENED_MISSING_INTERP = SCREENED | MISSING | (1 << 8) | (2 << 11)

        Reading individual fields from a retrieved flag::

            flag = quality_array[i, 0]
            screened     = bool(flag & 1)
            validity     = (flag >> 1) & 0b1111   # 1=okay,2=missing,4=questionable,8=reject
            data_range   = (flag >> 5) & 0b11
            rev_cause    = (flag >> 8) & 0b111
            rep_method   = (flag >> 11) & 0b1111
            test_failure = (flag >> 15) & 0b11111111111   # bits 16-26
            protected    = bool(flag & (1 << 31))

        Note
        ----
        DSS-6 supports only a single quality integer per value (element size = 1).
        Passing an array with element size > 1 to a DSS-6 file raises a ``ValueError``
        at write time. DSS-7 supports element size > 1, though older programs may not
        read multi-integer quality flags correctly.

        Parameters
        ----------
        data : array-like of int or None
            * 1-D array of shape ``(count,)`` - one quality integer per value
              (element size = 1).
            * 2-D array of shape ``(count, element_size)`` - multiple quality integers
              per value.
            * ``None`` clears quality flags.

        Returns
        -------
        numpy.ndarray of int32 with shape ``(count, element_size)``, or ``None``.

        Raises
        ------
        ValueError
            If the first dimension does not match ``count``.

        Examples
        --------
        Three-point regular time series with one quality integer per value:

        >>> from pydsstools.core import TimeSeriesContainer
        >>> tsc = TimeSeriesContainer(
        ...     "/BASIN/GAGE/FLOW//1HOUR/OBS/",
        ...     count=3, interval=1,
        ...     values=[100.5, 95.2, -901.0],
        ...     start_time="01JAN2020 0100",
        ...     data_units="ft", data_type="INST-VAL",
        ... )
        >>> # Bit 1 (screened) must be set before any other bit is meaningful.
        >>> # Bits 2-5 encode validity; only one validity bit may be set at a time.
        >>> SCREENED_OKAY         = 0b00000011  # 3  — screened and valid
        >>> SCREENED_QUESTIONABLE = 0b00001001  # 9  — screened, under review
        >>> SCREENED_MISSING      = 0b00000101  # 5  — screened, value is missing
        >>> tsc.quality_flags = [SCREENED_OKAY, SCREENED_QUESTIONABLE, SCREENED_MISSING]
        """
        return self._quality_flags

    @quality_flags.setter
    def quality_flags(self, data):
        if data is None:
            self._quality_flags = None
            self._quality_elem_size = 0
            return
        arr = np.ascontiguousarray(data, dtype=np.int32)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if arr.ndim != 2:
            raise ValueError("quality_flags must be 1-D or 2-D")
        if arr.shape[0] != self._count:
            raise ValueError(
                f"quality_flags first dimension ({arr.shape[0]}) must match count ({self._count})")
        self._quality_flags = arr
        self._quality_elem_size = arr.shape[1]
        self._quality_mv = arr.ravel()
        self._quality_ptr = &self._quality_mv[0]

    @property
    def integer_notes(self):
        """
        Fixed-length integer notes for the time series values.

        Integer notes provide structured integer metadata alongside each value —
        for example, a sensor ID, a flag code, or a revision counter. Each value
        has a fixed number of integers (the element size).

        Integer notes and text notes are mutually exclusive for a given time series
        record. Only one type can be stored at a time.

        Parameters
        ----------
        data : array-like of int or None
            * 1-D array of shape ``(count,)`` — one integer note per value
              (element size = 1).
            * 2-D array of shape ``(count, element_size)`` — multiple integers
              per value.
            * ``None`` clears integer notes.

        Returns
        -------
        numpy.ndarray of int32 with shape ``(count, element_size)``, or ``None``.

        Raises
        ------
        ValueError
            If the first dimension does not match ``count``, or if ``text_notes``
            is already set.

        Examples
        --------
        >>> tsc.integer_notes = [101, 102, 103]   # one int note per value

        Two integer notes per value:

        >>> import numpy as np
        >>> tsc.integer_notes = np.array([[1, 0], [2, 1], [3, 0]], dtype=np.int32)
        """
        return self._integer_notes

    @integer_notes.setter
    def integer_notes(self, data):
        if data is None:
            self._integer_notes = None
            self._inote_elem_size = 0
            return
        if self._text_notes_buf is not None:
            raise ValueError("Cannot set integer_notes when text_notes is already set")
        arr = np.ascontiguousarray(data, dtype=np.int32)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if arr.ndim != 2:
            raise ValueError("integer_notes must be 1-D or 2-D")
        if arr.shape[0] != self._count:
            raise ValueError(
                f"integer_notes first dimension ({arr.shape[0]}) must match count ({self._count})")
        self._integer_notes = arr
        self._inote_elem_size = arr.shape[1]
        self._inotes_mv = arr.ravel()
        self._inotes_ptr = &self._inotes_mv[0]

    @property
    def text_notes(self):
        """
        Variable-length text notes for the time series values.

        Text notes provide a free-text comment per value — for example,
        ``"manual edit"``, ``"sensor malfunction"``, or an empty string when
        no comment applies. Every value must have exactly one note entry, even
        if it is an empty string.

        Notes are stored internally as a single ASCII buffer with each note
        separated by a null character (``\\0``). Empty notes are preserved at
        their index.

        Integer notes and text notes are mutually exclusive for a given time series
        record. Only one type can be stored at a time.

        Parameters
        ----------
        notes : list of str or None
            List of ASCII strings, one per value. Length must equal ``count``.
            Empty strings are allowed. ``None`` clears text notes.

        Returns
        -------
        list of str, one per value, or ``None``.

        Raises
        ------
        ValueError
            If ``len(notes)`` does not match ``count``, or if ``integer_notes``
            is already set.
        UnicodeEncodeError
            If any note contains non-ASCII characters.

        Examples
        --------
        >>> tsc.text_notes = ["ok", "manual edit", "", "sensor fault", "ok"]

        Clear notes:

        >>> tsc.text_notes = None
        """
        if self._text_notes_buf is None:
            return None
        return [s.decode('ascii') for s in self._text_notes_buf.split(b'\0')[:self._count]]

    @text_notes.setter
    def text_notes(self, notes):
        if notes is None:
            self._text_notes_buf = None
            self._cnotes_length = 0
            return
        if self._integer_notes is not None:
            raise ValueError("Cannot set text_notes when integer_notes is already set")
        if len(notes) != self._count:
            raise ValueError(
                f"text_notes length ({len(notes)}) must match count ({self._count})")
        buf = '\0'.join(str(n) for n in notes) + '\0'
        self._text_notes_buf = buf.encode('ascii')
        self._cnotes_length = len(self._text_notes_buf)

    @property
    def vdi(self):
        """Return the :class:`~pydsstools.core.vdi.VerticalDatumInfo` to write
        into the DSS user header, or ``None`` if not set."""
        return self._vdi

    @vdi.setter
    def vdi(self, value):
        if value is None:
            self._vdi = None
            return
        from pydsstools.core.vdi import VerticalDatumInfo
        if not isinstance(value, VerticalDatumInfo):
            raise TypeError(
                f"Expected VerticalDatumInfo or None, got {type(value).__name__}"
            )
        self._vdi = value

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
            # VDI write
            verticalDatumInfo vdi_c
            char *xml_ptr
            char *err_msg
            int *uh_ptr
            int uh_num

        if self._values is None:
            raise ValueError("Timeseries values is not defined")

        val_ptr = self._values_ptr

        if interval > 0:
            # Regular Timeseries
            if self.start_time is None:
                raise ValueError(f"start_time value for regular timeseries is must be specified, got None.")
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
            # _times_mv always stores absolute minutes from Julian day 0 (Dec 31 1899).
            # This is true regardless of what _julian_base the user supplied:
            #   - HecTime/str/datetime inputs → HecTime.value() → absolute minutes
            #   - HecTime(int, julian_base=X) converts relative→absolute at construction,
            #     so value() still returns absolute; the base is consumed at that point
            #   - Raw int inputs are stored as-is, but DSS interprets them with ibdate=0
            # zStructTimeSeries.times[] must be offsets from julianBaseDate, so
            # julianBaseDate=0 (epoch) is the only correct choice here.
            # Only pass startDateBase when _julian_base is the epoch (julian=0) to
            # be explicit; any other value would cause ztsStore to double-count the
            # base when computing stored dates.
            if isinstance(self._julian_base, HecTime) and self._julian_base.julian() == 0:
                _julian_base = self._julian_base.date()
                julian_base = _julian_base

            tss = zstructTsNewIrregFloats(pathname,val_ptr, count,
                                          time_ptr, granularity,
                                          julian_base,
                                          data_units,data_type)
        if self._tzid:
            tss[0].timeZoneName = self._ctzid

        if self._quality_flags is not None:
            tss[0].quality = self._quality_ptr
            tss[0].qualityElementSize = self._quality_elem_size

        if self._integer_notes is not None:
            tss[0].inotes = self._inotes_ptr
            tss[0].inoteElementSize = self._inote_elem_size
        elif self._text_notes_buf is not None:
            tss[0].cnotes = PyBytes_AS_STRING(self._text_notes_buf)
            tss[0].cnotesLengthTotal = self._cnotes_length

        if self._vdi is not None:
            xml_ptr = NULL
            err_msg = NULL
            uh_ptr = NULL
            uh_num = 0
            initializeVerticalDatumInfo(&vdi_c)
            _bnd = self._vdi.native_datum.encode("ascii")
            _bu  = self._vdi.unit.encode("ascii")
            memcpy(vdi_c.nativeDatum, PyBytes_AS_STRING(_bnd), len(_bnd))
            vdi_c.nativeDatum[len(_bnd)] = 0
            memcpy(vdi_c.unit, PyBytes_AS_STRING(_bu), len(_bu))
            vdi_c.unit[len(_bu)] = 0
            if self._vdi.offset_to_navd88 is not None:
                vdi_c.offsetToNavd88 = <double>self._vdi.offset_to_navd88
                vdi_c.offsetToNavd88IsEstimate = 1 if self._vdi.navd88_is_estimate else 0
            if self._vdi.offset_to_ngvd29 is not None:
                vdi_c.offsetToNgvd29 = <double>self._vdi.offset_to_ngvd29
                vdi_c.offsetToNgvd29IsEstimate = 1 if self._vdi.ngvd29_is_estimate else 0
            err_msg = verticalDatumInfoToString(&xml_ptr, &vdi_c, 0)
            if err_msg != NULL:
                _err = (<bytes>err_msg).decode("ascii", "replace")
                free(err_msg)
                raise RuntimeError(f"verticalDatumInfoToString: {_err}")
            uh_ptr = stringToUserHeader(xml_ptr, &uh_num)
            free(xml_ptr)
            if uh_ptr == NULL:
                raise MemoryError("stringToUserHeader: memory allocation failed")
            tss[0].userHeader = uh_ptr
            tss[0].userHeaderNumber = uh_num
            tss[0].allocated[4] = 1  # zSTRUCT_userHeader=4: tells zstructFree to free uh_ptr

        ts_st = createTSS(tss)
        #logger.debug("length = {}".format(ts_st.count))
        return ts_st  
