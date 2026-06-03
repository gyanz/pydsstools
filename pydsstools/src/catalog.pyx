cdef CatalogStruct createCatalog(zStructCatalog *cts):
    """Creates time-series struct
    
    Returns
    -------
        # CatalogStruct class

    Usage
    -----
        # Available only in extension scripts
    """
    ct_st = CatalogStruct()
    if cts:
        if cts[0].numberPathnames>=1:
            ct_st.cts = cts 
        else:
            zstructFree(cts)            
            cts=NULL
    return ct_st   


cdef class CatalogStruct:
    """ 
    Python Extension class container for pathnames catalog retrieved from HEC-DSS file.

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
        >>> ct_st = CatalogStruct()            
        >>> ct_st.cts = cts # where cts is pointer to HEC-DSS zStructCatalog

    """
    cdef:
        zStructCatalog *cts

    def __cinit__(self,*arg,**kwargs):
        self.cts=NULL

    cpdef int count(self):
        cdef int num = 0
        if self.cts:
            num = self.cts[0].numberPathnames
        return num 

    cpdef list paths(self):
        cdef:
            list pathnames = []
            int count = 0
            int i 

        if self.cts:
            count = self.count()
            if count > 0:
                for i in range(0,count):
                    pathnames.append(self.cts[0].pathnameList[i])

        return pathnames

    cpdef list attributes(self,bint parse=False):
        cdef:
            list values = []
            char* value
            int count = 0
            int i 

        if self.cts:
            count = self.count()
            i = self.cts.boolHasAttribues
            if count > 0 and i:
                for i in range(0,count):
                    value = self.cts[0].attributes[i]
                    val = (<bytes>value).decode("ascii","ignore")
                    values.append(val)
                
                if parse:
                    _values = []
                    for val in values:
                        attr = {}
                        for val in val.split(";;"):
                            k,v = val.split("::")
                            attr[k] = v
                        _values.append(attr)
                    values = _values

        return values

    cpdef list typecodes(self):
        cdef:
            list values = []
            int count
            int i 

        if self.cts:
            count = self.count()
            if count > 0:
                for i in range(0,count):
                    values.append(self.cts[0].recordType[i])

        return values
    
    cpdef list start_dates(self):
        cdef:
            list values = []
            int count, i
        
        if self.cts:
            i = self.cts[0].boolIncludeDates
            count = self.count()
            if i and count > 0:
                for i in range(count):
                    values.append(self.cts[0].startDates[i])
        return values

    cpdef list end_dates(self):
        cdef:
            list values = []
            int count, i
        
        if self.cts:
            i = self.cts[0].boolIncludeDates
            count = self.count()
            if i and count > 0:
                for i in range(count):
                    values.append(self.cts[0].endDates[i])
        return values

    cpdef list last_write_times(self):
        cdef:
            list values = []
            int count, i
        
        if self.cts:
            i = self.cts[0].lastWriteTimeSearch
            count = self.count()
            if i and count > 0 :
                for i in range(count):
                    values.append(self.cts[0].lastWriteTimeRecord[i])
        return values

    @staticmethod
    def new_rts(Open fid,
                str pathname,
                bint sort=0,
                int status_wanted=0,
                int max_count=0,
                int last_write_time_search=0,
                int last_write_time_search_flag=0,
                bint include_dates = 0
                ):
        
        return CatalogStruct.new(fid,pathname,
                                sort=sort,
                                status_wanted=status_wanted,
                                max_count=max_count,
                                record_type_code_start=100,
                                record_type_code_end=107,
                                last_write_time_search = last_write_time_search,
                                last_write_time_search_flag = last_write_time_search_flag,
                                include_dates = include_dates
                                )

    @staticmethod
    def new_its(Open fid,
                str pathname,
                bint sort=0,
                int max_count=0,
                int status_wanted=0,
                int last_write_time_search=0,
                int last_write_time_search_flag=0,
                bint include_dates = 0
                ):
        
        return CatalogStruct.new(fid,pathname,record_type_code_start=110,record_type_code_end=117)

    @staticmethod
    def new_pd(Open fid,
               str pathname,
               bint sort=0,
               int status_wanted=0,
               int max_count=0,
               int last_write_time_search=0,
               int last_write_time_search_flag=0,
               bint include_dates = 0
               ):
        
        return CatalogStruct.new(fid,pathname,record_type_code_start=200,record_type_code_end=205)

    @staticmethod
    def new(Open fid,
            str pathname,
            bint sort=0,
            int max_count=0,
            int status_wanted=0,
            int record_type_code_start=0,
            int record_type_code_end=0,
            #bint collection=0,
            int last_write_time_search=0,
            int last_write_time_search_flag=0,
            bint include_dates = 0
            ):
        cdef:
            long long *ifltab = fid.ifltab
            char *cpathname = pathname
            zStructCatalog *cts = NULL
            CatalogStruct ct_st
            int path_count = 0

        # last_write_time_search == 0 for ignore (default)
        # last_write_time_search_flag:
        #  -2:  time <  lastWriteTimeSearch
        #  -1:  time <= lastWriteTimeSearch
        #   0:  time == lastWriteTimeSearch
        #   1:  time >= lastWriteTimeSearch
        #   2:  time >  lastWriteTimeSearch

        #if "*" in pathname and collection:
        #    logger.warning(f"Wild card expression in pathname is not allowed when collection flag is set: {pathname}.")
        #    return
        
        if record_type_code_start < 0 or record_type_code_end < 0:
            logger.warning("Negative code of record type is not valid")
            return

        if record_type_code_start > record_type_code_end:
            logger.warning("record type code for start can not be greater than type code of end.")
            return
        
        if not status_wanted in (0,1,2,11,12,100):
            logger.warning("status_wanted must be 0 (all valid includes primary and alaises), 1 (primary only), 2 (allias only), 11 (deleted only), 12 (renamed only) or 100 (any, deleted, renamed ..).")
            return

        if last_write_time_search:
            if not last_write_time_search_flag in (-2,-1,0,1,2):
                logger.warning(f"Expected values for last_write_time_search_flag are -2,-1,0,1 and 2; got '{last_write_time_search_flag}'.")
                return

        if max_count < 0:
            logger.warning("Maximum number of paths is less than 0. Valid values are 0 or greater. Specify 0 to return all matching paths.")

        cts = zstructCatalogNew()

        if cts == NULL:
            logger.warning("Error while create Catalog object.")
            return

        cts[0].statusWanted = status_wanted 
        cts[0].typeWantedStart = record_type_code_start 
        cts[0].typeWantedEnd = record_type_code_end
        cts[0].lastWriteTimeSearch = last_write_time_search
        cts[0].boolIncludeDates = include_dates

        if last_write_time_search:
            cts[0].lastWriteTimeSearchFlag = last_write_time_search_flag

        path_count = zcatalog(ifltab,pathname,cts,sort)

        if path_count < 0:
            logger.warning("Error while create Catalog object.")
            return
        
        if path_count == 0:
            logger.debug("No matching dss paths found.")
            return

        ct_st = createCatalog(cts)
        return ct_st

    # No NULL pointer check for above function
    # NULL check with following functions
    def __dealloc__(self):
        if self.cts:
            zstructFree(self.cts)

cpdef CatalogStruct get_pathname_catalog(Open fid, str path_with_wild, bint sort=0,
                                        int status_wanted=0, int type_wanted_start=0, int type_wanted_end=0):
    cdef:
        long long *ifltab = fid.ifltab
        char *pathname = path_with_wild
        zStructCatalog *cts = NULL
        CatalogStruct ct_st
        int negative_or_numberPathnames = 0

    # set warning with this check??
    cts = zstructCatalogNew()
    #if status_wanted or type_wanted_start or type_wanted_end:
    cts[0].statusWanted = status_wanted
    cts[0].typeWantedStart = type_wanted_start
    cts[0].typeWantedEnd = type_wanted_end

    negative_or_numberPathnames = zcatalog(ifltab, pathname, cts, sort)
    if negative_or_numberPathnames < 0:
       logger.warning('Error with retrieving catalog, CODE = %d' % negative_or_numberPathnames)
    #print('zcatalog return = %d'% negative_or_numberPathnames)
    ct_st = createCatalog(cts)
    return ct_st


