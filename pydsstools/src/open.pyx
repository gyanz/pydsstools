# TODO: Improve error check and messaging

cdef class Open:
    """Returns file handle to a dss file that can be used to read from or write
       to that file.  

    Parameters
    ----------
        # dssFilename: ascii encoded dss file path
        # version:  
            # 6 or 7 to specify function call method associated with dss 6
              or 7 library version. 
            # If empty or any other number is specified, the version is selected 
              automatically. If the file does not exist, new file is created 
              using version 7 dss library.  
    """
    cdef:
        long long ifltab[500]
        readonly int version
        readonly int file_status
        readonly int read_status
        readonly int write_status

    def __init__(self,dssFilename,version=None):
        if version == 6:
            self.file_status = zopen6(self.ifltab, dssFilename)
        elif version == 7:
            self.file_status = zopen7(self.ifltab, dssFilename)
        else:
            self.file_status = zopen(self.ifltab, dssFilename)
        isError(self.file_status)
        self.version = zgetVersion(self.ifltab)

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_val,tb):
        self.close()

    def close(self):
        if self.ifltab != NULL:
            zclose(self.ifltab)

    def __version__(self):
        return    
        #return zgetFullVersion(self.ifltab)        

    def get_status(self):
        return (self.file_status,self.read_status,self.write_status)

    cpdef TimeSeriesStruct read_path(self,char *pathname,int retrieveFlag=-1,
                                        int boolRetrieveDoubles=1,
                                        int boolRetrieveQualityNotes=0, int boolRetrieveAllTimes=0):
        """Read time-series data from the dss file handle

        Parameter
        ---------
            pathname: ascii encoded string
                dss pathname to retieve data from

            retrieveFlag: int, default -1 (reg), 0 (irreg)
                Regular -> 0 (adhere to time-window), 
                           -1 (trim missing data at beginning and end, not inside),
                Irregular -> 0 (adhere),
                             1 (trim or retrieve one value before?),
                             2(Retrieve one value after end),
                             3 (Retrieve one value before and after time window)     

            retrieveDoublesFlag: int, default 0
                    0 -> retrieve values as stored, if missing return as double
                    1 -> retrieve as floats
                    2 -> retrieve as doubles

            boolRetrieveQualityNotes: bool or int, default 0
                    0 -> do not retrieve quality and notes
                    1 -> retrieve quality notes, if they exist

        Returns
        ---------
            # TimeSeriesStruct class object
        
        Usage
        -----
            >>>with Open(b"sample.dss") as fid:
            ...     tsc=fid.read(dsspath,*arg,**kwargs)

        """
        cdef:
            zStructTimeSeries *ztss=NULL 
        ztss = zstructTsNew(pathname)

        if boolRetrieveAllTimes: 
            ztss[0].boolRetrieveAllTimes = 1

        self.read_status = ztsRetrieve(self.ifltab,ztss,retrieveFlag,
                                       boolRetrieveDoubles,
                                       boolRetrieveQualityNotes)
        
        isError(self.read_status)

        if boolRetrieveDoubles == 1:
            ztss[0].doubleValues = NULL
        elif boolRetrieveDoubles == 2:  
            ztss[0].floatValues = NULL

        tss = createTSS(ztss)
        return tss 

    cpdef TimeSeriesStruct read_window(self,char *pathname,char *startDate,
                                            char *startTime,char *endDate,
                                            char *endTime,
                                            int retrieveFlag=-1,
                                            int boolRetrieveDoubles=1,
                                            int boolRetrieveQualityNotes=0):


        cdef:
            zStructTimeSeries *ztss=NULL 
        ztss = zstructTsNewTimes(pathname,startDate,startTime,endDate,endTime)
        self.read_status = ztsRetrieve(self.ifltab,ztss,retrieveFlag,
                                       boolRetrieveDoubles,
                                       boolRetrieveQualityNotes)
        
        isError(self.read_status)

        if boolRetrieveDoubles == 1:
            ztss[0].doubleValues = NULL
        elif boolRetrieveDoubles == 2:  
            ztss[0].floatValues = NULL

        tss = createTSS(ztss)
        return tss 

    cpdef TimeSeriesStruct put(self,TimeSeriesContainer tsc,int storageFlag=0):
        cdef:
            TimeSeriesStruct ts_st
            zStructTimeSeries *tss
            int status
        tsc.setValues()
        ts_st = createNewTimeSeries(tsc)
        tss = ts_st.tss
        if tss == NULL:
            logging.error("Failed to write time-series")
            return
        self.write_status = ztsStore(self.ifltab,tss,storageFlag)
        isError(self.write_status) 
        return ts_st

    cpdef int copyRecordsFrom(self,Open copyFrom,str pathnameFrom,str pathnameTo="") except *:
        cdef int status
        if not pathnameTo:
            pathnameTo = pathnameFrom
        status = copyRecord(copyFrom,self,pathnameFrom,pathnameTo)
        return status

    cpdef int copyRecordsTo(self,Open copyTo,str pathnameFrom, str pathnameTo="") except *:
        cdef int status
        if not pathnameTo:
            pathnameTo = pathnameFrom
        status = copyRecord(self,copyTo,pathnameFrom,pathnameTo)
        return status


    cpdef PairedDataStruct read_pd(self,char *pathname, tuple window = None):
        # Read paired data from the given pathname
        cdef:
            zStructPairedData *zpds=NULL 
            int retrieveSizeFlag = 1 # retrieve as float
            int data_no, curve_no
            int start_ord, end_ord, start_curve, end_curve

        #curve_no,data_no,_,_ = pd_size(self.ifltab,pathname)
        #last_ord = data_no
        #last_curve = curve_no

        zpds = zstructPdNew(pathname)

        if window:
            start_ord, end_ord, start_curve, end_curve = window        
            zpds[0].startingOrdinate = start_ord
            zpds[0].endingOrdinate = end_ord
            zpds[0].startingCurve = start_curve
            zpds[0].endingCurve = end_curve

        self.read_status = zpdRetrieve(self.ifltab,zpds,retrieveSizeFlag)

        isError(self.read_status)

        pd_st = createPDS(zpds)
        return pd_st 

    cpdef int prealloc_pd(self, PairedDataContainer pdc,int label_size) except *:
        # When preallocating pd, it is important to know how much size to allocate
        #   for the labels
        # label_size = number of characters in label for a curve in pd
        # When it is 0, default size is used
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int status
        pdc.setValues(mode=0,label_size = label_size)
        pd_st = preallocNewPairedData(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,10)
        isError(self.write_status)
        pdc.curves_ptr = NULL
        pdc.curves_mv = None

    cpdef int put_one_pd(self, PairedDataContainer pdc,int i,tuple window = None, int label_size = 0) except *:
        # i = ith curve no to save in the file, 1 >= i <= curve_no
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int start_ord,end_ord

        if label_size > 0:
            label_size = self.pd_info(pdc.pathname)['label_size']
        pdc.setValues(mode = 1,label_size = label_size)
        data_no_user = pdc.curves_mv.shape[1]

        if not window:
            pd_st = createOnePairedData(self.ifltab,pdc,i)
        else:
            start_ord,end_ord = window
            pd_st = createOnePairedData(self.ifltab,pdc,i,start_ord,end_ord)

        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,11)
        isError(self.write_status)
        pdc.curves_ptr = NULL
        pdc.curves_mv = None

    cpdef int put_pd(self, PairedDataContainer pdc) except *:
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int status
        pdc.setValues(mode=-1)
        pd_st = createNewFloatPairedData(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,0)
        isError(self.write_status)
        pdc.curves_ptr = NULL
        pdc.curves_mv = None

    cpdef void read_grid(self,const char *pathname, SpatialGridStruct sg_st, int boolRetrieveData=1) except *:
        cdef:
            zStructSpatialGrid *zsgs = NULL 
        zsgs = zstructSpatialGridNew(pathname)
        #self.read_status = zspatialGridRetrieve(self.ifltab,zsgs,boolRetrieveData)
        self.read_status = RetrieveGriddedData_wrap(self.ifltab,zsgs,boolRetrieveData)
        isError(self.read_status)
        updateSGS(sg_st,zsgs)

    cpdef int put_grid(self,str pathname, np.ndarray data, float nodata, dict stats, dict profile) except *:
        # TODO: Error check
        saveSpatialGrid(self.ifltab,pathname, data, nodata, stats, profile)

    cpdef dict dss_info(self, str pathname):
        return dss_info(self,pathname)

    cpdef dict pd_info(self, str pathname):
        result = pd_size(self,pathname) 
        data = {}
        data['curve_no'] = result[0]
        data['data_no'] = result[1]
        data['dtype'] = result[3]
        data['label_size'] = result[4]
        return data

    cpdef int _record_type_code(self,str pathname):
        cdef int typecode
        typecode = zdataType(self.ifltab,pathname)
        return typecode

    cpdef str _record_type(self,str pathname):
        cdef:
            int typecode
            str dtype

        typecode = zdataType(self.ifltab,pathname)

        if typecode >= 100 and typecode < 200:
            dtype = 'TS'

        elif typecode >= 200 and typecode < 300:
            dtype = 'PD'

        elif typecode >= 400 and typecode < 450:
            dtype = 'GRID'

        else:
            dtype = 'OTHER'

        return dtype

    def __dealloc__(self):
        if self.ifltab != NULL:
            zclose(self.ifltab)
