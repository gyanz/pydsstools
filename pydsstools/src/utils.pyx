'''
cdef class dss_info:
    zStructRecordSize *recordSize
    # All data
    readonly int dataType
    readonly bytes data_type
    readonly int version
    readonly int numberValues
    readonly int logicalNumberValues
    # TS
    readonly int numberRecordsFound
    readonly int tsValueSize
    readonly int tsValueElementSize        
    # PD
    readonly pd_curve_no
    readonly pd_data_no
    readonly ipdValueSize
    #readonly pdBoolIndependentIsXaxis
    readonly int pdLabelsLength
    readonly int status 

cdef int copyRecord(Open copyFrom, Open copyTo, str pathnameFrom, str pathnameTo):

cpdef int copyRecordTo(Open copyFrom, str copyToFile, str pathnameFrom, str pathnameTo):

'''
def str2ascii(file):
    if isinstance(file,str):
        return file.encode('ascii')
    elif isinstance(file,bytes):
        return file
    else:
        logging.error("Wrong filename or encoding (not ascii or byte) ")

cdef class dss_info:
    cdef: 
        zStructRecordSize *recordSize
        # All data
        readonly int dataType
        readonly bytes data_type
        readonly int version
        readonly int numberValues
        readonly int logicalNumberValues
        # TS
        readonly int numberRecordsFound
        readonly int tsValueSize
        readonly int tsValueElementSize        
        # PD
        readonly pd_curve_no
        readonly pd_data_no
        readonly ipdValueSize
        #readonly pdBoolIndependentIsXaxis
        readonly int pdLabelsLength
        readonly int status 

    def __init__(self,Open fid,char *pathname):
        self.recordSize = zstructRecordSizeNew(pathname)
        self.status = zgetRecordSize(fid.ifltab,self.recordSize)
        if not self.status == 0: # STATUS_OK != 0
            zstructFree(self.recordSize)
            self.recordSize=NULL
            raise BaseException("Seems invalid Data Size Query!!")

        self.dataType = self.recordSize[0].dataType
        if self.dataType == 200:
            self.data_type = b'float32'
        elif self.dataType == 205:
            self.data_type = b'double'
        else:
            self.data_type = b'unknown'

        self.version = self.recordSize[0].version
        self.numberRecordsFound = self.recordSize[0].numberRecordsFound
        self.tsValueSize = self.recordSize[0].tsValueSize
        self.tsValueElementSize = self.recordSize[0].tsValueElementSize
    
        self.pd_curve_no = self.recordSize[0].pdNumberCurves # bug: this is giving data_no
        self.pd_data_no = self.recordSize[0].pdNumberOrdinates # bug: this is giving curve_no
        self.ipdValueSize = self.recordSize[0].ipdValueSize
        self.pdLabelsLength = self.recordSize[0].pdLabelsLength


cdef int copyRecord(Open copyFrom, Open copyTo, str pathnameFrom, str pathnameTo):
    """Copy a record from one hec-dss file (From-) to another (To-)

    Parameter
    ----------
        copyFrom: "Open" class handle to hec-dss file where the data exist
        copyTo: "Open" class handle to destination hec-dss file
        pathnameFrom: dss pathname of the data to be copied
        pathnameTo: the pathname of the data in the desination dss file

    Usage
    -------
        Only available to cython scripts

    Returns
    --------
        integer status
    """
    cdef:
        long long *ifltabFrom = copyFrom.ifltab
        long long *ifltabTo = copyTo.ifltab

    cdef:
        char *pathFrom = pathnameFrom
        char *pathTo = pathnameTo
        int status
    status = zcopyRecord(ifltabFrom,ifltabTo,pathFrom,pathTo)
    return status

cpdef int copyRecordTo(Open copyFrom, str copyToFile, str pathnameFrom, str pathnameTo):
    """Copy a record from one hec-dss file (From-) to another (To-)

    Parameter
    ----------
        copyFrom: "Open" class handle to hec-dss file where the data exist
        copyTo: sting file path to destination hec-dss file
        pathnameFrom: dss pathname of the data to be copied
        pathnameTo: the pathname of the data in the desination dss file

    Usage
    -------
        Available to both cython and CPython scripts

    Returns
    --------
        integer status
    """

    cdef:
        long long *ifltabFrom = copyFrom.ifltab
        long long *ifltabTo=NULL
        Open fid
    cdef:
        char *pathFrom = pathnameFrom
        char *pathTo = pathnameTo
        int status
    with Open(copyToFile) as fid:
        ifltabTo = fid.ifltab
        status = zcopyRecord(ifltabFrom,ifltabTo,pathFrom,pathTo)
        return status

cpdef int get_grid_version(Open _open, str pathname):
    cdef:
        long long *ifltab= _open.ifltab
        const char *path = pathname
        int *zversion = <int*>malloc(sizeof(int*))
        int ver = -9999
        int status
    status = zspatialGridRetrieveVersion(ifltab,path,zversion)
    if zversion:
        ver = zversion[0]
        free(zversion)
    return ver

class DssPathName(object):
    def __init__(self,pathname):
        self.pathname = pathname
        self.pathname_parts = []
        self.parse()

    def parse(self):
        if not self.pathname:
            logging.warn('Invalid dss pathname')
            self.pathname = '/A/B/C/D/E/F/'

        if isinstance(self.pathname, DssPathName):
            self.pathname = self.pathname.pathname    
            
        if (not self.pathname[0] == '/') or (not self.pathname[-1] == '/'):
            #logging.error('Invalid dss pathname: not starting or ending with character "/"',exc_info=True)
            logging.info('%s',self.pathname)
            logging.error('Invalid dss pathname: not starting or ending with character "/"')
            raise DssPathException('Invalid dss pathname: not starting or ending with character "/"')

        parts = self.pathname.split('/')[1:-1]
        if not len(parts) == 6:
            #logging.error('Invalid dss pathname: No of pathname parts not equal to six',exc_info=True)
            logging.error('Invalid dss pathname: No of pathname parts not equal to six')
            raise DssPathException('Invalid dss pathname: No of pathname parts not equal to six')

        self.pathname_parts = parts

    def __repr__(self):
        string_rep = '/'
        for x in self.pathname_parts:
            string_rep += x + '/'
        return string_rep

    def text(self):
        return self.__repr__()

    def setAPart(self,A):
        self.pathname_parts[0]=A

    def setBPart(self,B):
        self.pathname_parts[1]=B

    def setCPart(self,C):
        self.pathname_parts[2]=C

    def setDPart(self,D):
        self.pathname_parts[3]=D

    def setEPart(self,E):
        self.pathname_parts[4]=E

    def setFPart(self,F):
        self.pathname_parts[5]=F

    def getAPart(self):
        return self.pathname_parts[0]

    def getBPart(self):
        return self.pathname_parts[1]

    def getCPart(self):
        return self.pathname_parts[2]

    def getDPart(self):
        return self.pathname_parts[3]

    def getEPart(self):
        return self.pathname_parts[4]

    def getFPart(self):
        return self.pathname_parts[5]

