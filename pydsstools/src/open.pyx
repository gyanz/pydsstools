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
        readonly str filename
        readonly int file_status
        readonly int read_status
        readonly int write_status

    def __init__(self,dssFilename,version=None):
        if version == 6:
            self.file_status = zopen6(self.ifltab, dssFilename)
        elif version == 7:
            self.file_status = zopen7(self.ifltab, dssFilename)
        else:
            self.file_status = hec_dss_zopen(self.ifltab, dssFilename)
        isError(self.file_status)
        self.version = zgetVersion(self.ifltab)
        self.filename = dssFilename

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
    """
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
    """
    cpdef void put(self,TimeSeriesContainer tsc,int storageFlag=0):
        cdef:
            TimeSeriesStruct ts_st
            zStructTimeSeries *tss
            int status
        ts_st = tsc.create_tss()
        tss = ts_st.tss
        if tss == NULL:
            logging.error("Failed to write time-series")
            return
        self.write_status = ztsStore(self.ifltab,tss,storageFlag)
        isError(self.write_status)
        #return self.write_status

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
        # indexes are 0-bases while it is 1-based in c code
        cdef:
            zStructPairedData *zpds=NULL 
            # retrieve as float
            int rsize_flag = 1
            int rows, cols
            int row_start, row_end, col_start, col_end

        zpds = zstructPdNew(pathname)

        if window:
            row_start, row_end, col_start, col_end = window        
            zpds[0].startingOrdinate = row_start + 1
            zpds[0].endingOrdinate = row_end + 1
            zpds[0].startingCurve = col_start + 1
            zpds[0].endingCurve = col_end + 1

        self.read_status = zpdRetrieve(self.ifltab,zpds,rsize_flag)
        isError(self.read_status)
        pd_st = createPDS(zpds)
        return pd_st 

    cpdef int prealloc_pd(self, PairedDataContainer pdc) except *:
        # When preallocating pd, it is important to know how much size to allocate
        #   for the labels
        # label_size = number of characters in label for a curve in pd
        # When it is 0, default size is used
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int status

        pdc.set_clabels(pdc_mode.allocate)
        pd_st = write_allocate_pdata(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,10)
        isError(self.write_status)
        #pdc._ydata_ptr = NULL
        #pdc.y_data_mv = None

    cpdef int put_one_pd(self, PairedDataContainer pdc,int col_index, tuple row_window = None) except *:
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int row_start, row_end
            int label_size

        label_size = self.pd_info(pdc.pathname)['label_size']
        pdc.set_clabels(pdc_mode.one,label_size)

        if not row_window:
            pd_st = write_one_pdata(self.ifltab,pdc,col_index)
        else:
            row_start,row_end = row_window
            pd_st = write_one_pdata(self.ifltab,pdc,col_index,row_start,row_end)

        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,11)
        isError(self.write_status)
        #pdc.curves_ptr = NULL
        #pdc.curves_mv = None

    cpdef int put_pd(self, PairedDataContainer pdc) except *:
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            int status

        pdc.set_clabels(pdc_mode.normal)
        pd_st = write_normal_pdata(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab,zpds,0)
        isError(self.write_status)
        #pdc.curves_ptr = NULL
        #pdc.curves_mv = None

    cpdef void read_grid100(self,const char *pathname, SpatialGridStruct sg_st, bint retrieve_data) except *:
        cdef:
            zStructSpatialGrid *zsgs = NULL
        zsgs = zstructSpatialGridNew(pathname)
        isError(self.read_status)
        #self.read_status = RetrieveGriddedData_wrap(self.ifltab,zsgs,retrieve_data)
        self.read_status = zspatialGridRetrieve(self.ifltab,zsgs,retrieve_data)
        isError(self.read_status)
        updateSGS(sg_st,zsgs)

    cpdef void read_grid0(self,const char *pathname,SpatialGridStruct sg_st, object ginfo6, bint retrieve_data) except *:
        cdef:
            int status
            zStructSpatialGrid *zsgs = NULL
        zsgs = zstructSpatialGridNew(pathname)
        status = read_grid0_as_grid100(self.ifltab,zsgs,ginfo6,retrieve_data)
        print("status = ",status)
        updateSGS(sg_st,zsgs)

    cpdef np.ndarray _read_grid0_array(self,const char *pathname, object ginfo6, bint retrieve_data):
        cdef:
             np.ndarray data
        data =  read_grid0(self.ifltab,pathname,ginfo6,retrieve_data)
        return data   

    def _get_gridver(self,const char *pathname):
        ver = get_gridver_from_path(self.ifltab,pathname)
        if ver == -1:
            return
        return ver

    def _get_gridtype(self,const char *pathname):
        grid_type = get_gridtype_from_path(self.ifltab,pathname)
        if grid_type == -1:
            return
        return grid_type    

    cpdef int put_grid(self,str pathname, float[:,::1] data, object gridinfo7) except *:
        # TODO: Error check
        save_grid7(self.ifltab,pathname, data, gridinfo7)

    cpdef int put_grid0(self,str pathname,  float[:,::1] data, object gridinfo6) except *:
        # TODO: Error check
        save_grid0(self.ifltab,pathname, data, gridinfo6)

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
