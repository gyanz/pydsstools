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

    cpdef list getPathnameList(self):
        cdef:
            list pathList = []
            int num = self.numberPathnames()
            int i 

        if num:
            for i in range(0,num):
                pathList.append(self.cts[0].pathnameList[i])

        return pathList

    cpdef list getRecordType(self):
        cdef:
            list typeList = []
            int num = self.numberPathnames()
            int i 

        if num:
            #for i in range(0,num):
            typeList.append(self.cts[0].recordType[0])

        return typeList

    cpdef int numberPathnames(self):
        cdef int num = 0
        if self.cts:
            num = self.cts[0].numberPathnames
        return num 


    # No NULL pointer check for above function
    # NULL check with following functions

    def __dealloc__(self):
        if self.cts:
            zstructFree(self.cts)

cpdef CatalogStruct getPathnameCatalog(Open fid,str pathWithWild, int sort=0, 
                                       int statusWanted=0, int typeWantedStart=0, int typeWantedEnd=0):
    cdef:
        long long *ifltab = fid.ifltab
        char *pathname = pathWithWild
        zStructCatalog *cts = NULL
        CatalogStruct ct_st
        int negative_or_numberPathnames = 0

    # set warning with this check??
    cts = zstructCatalogNew()
    #if statusWanted or typeWantedStart or typeWantedEnd:
    cts[0].statusWanted = statusWanted 
    cts[0].typeWantedStart = typeWantedStart 
    cts[0].typeWantedEnd = typeWantedEnd  

    negative_or_numberPathnames = zcatalog(ifltab,pathname,cts,sort)
    if negative_or_numberPathnames < 0: 
       logging.warning('Error with retrieving catalog, CODE = %d' % negative_or_numberPathnames) 
    #print('zcatalog return = %d'% negative_or_numberPathnames) 
    ct_st = createCatalog(cts)
    return ct_st

cpdef int deletePathname(Open fid,str pathname):
    cdef:
        long long *ifltab = fid.ifltab
        const char *path_name = pathname
        int status

    status = zdelete(ifltab,path_name)
    return status

