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

cpdef void setMessageLevel(int methodID,int levelID):
    zsetMessageLevel(methodID, levelID)

cdef class dss_info:
    cdef: 
        zStructRecordSize *recordSize
        readonly int status 

        # All data
        readonly int dataType
        readonly str data_type # custom def
        readonly int version
        readonly int numberValues
        readonly int logicalNumberValues
        # TS
        readonly int values1Number
        readonly int numberRecordsFound
        readonly int itsTimePrecisionStored
        readonly int tsPrecision
        readonly int tsTimeOffset
        readonly int tsProfileDepthsNumber
        readonly int tsBlockStartPosition
        readonly int tsBlockEndPosition
        readonly int tsValueSize
        readonly int tsValueElementSize        
        # PD
        readonly pd_curve_no
        readonly pd_data_no
        readonly ipdValueSize
        readonly int pdLabelsLength
        readonly int pdBoolIndependentIsXaxis
        readonly int pdPrecision

    def __init__(self,Open fid,char *pathname):
        self.recordSize = zstructRecordSizeNew(pathname)
        self.status = zgetRecordSize(fid.ifltab,self.recordSize)
        if not self.status == 0: # STATUS_OK != 0
            zstructFree(self.recordSize)
            self.recordSize=NULL
            raise BaseException("Seems invalid Data Size Query!!")

        # ALL
        self.dataType = self.recordSize[0].dataType
        self.version = self.recordSize[0].version
        self.numberValues = self.recordSize[0].numberValues
        self.logicalNumberValues = self.recordSize[0].logicalNumberValues
        # TS
        self.values1Number = self.recordSize[0].values1Number
        self.numberRecordsFound = self.recordSize[0].numberRecordsFound
        self.itsTimePrecisionStored = self.recordSize[0].itsTimePrecisionStored
        self.tsPrecision = self.recordSize[0].tsPrecision
        self.tsTimeOffset = self.recordSize[0].tsTimeOffset
        self.tsProfileDepthsNumber = self.recordSize[0].tsProfileDepthsNumber
        self.tsBlockStartPosition = self.recordSize[0].tsBlockStartPosition
        self.tsBlockEndPosition = self.recordSize[0].tsBlockEndPosition
        self.tsValueSize = self.recordSize[0].tsValueSize
        self.tsValueElementSize = self.recordSize[0].tsValueElementSize
        # PD 
        self.pd_curve_no = self.recordSize[0].pdNumberCurves 
        self.pd_data_no = self.recordSize[0].pdNumberOrdinates 
        self.ipdValueSize = self.recordSize[0].ipdValueSize
        self.pdLabelsLength = self.recordSize[0].pdLabelsLength
        self.pdBoolIndependentIsXaxis = self.recordSize[0].pdBoolIndependentIsXaxis
        self.pdPrecision = self.recordSize[0].pdPrecision

    def __dealloc__(self):
        if self.recordSize != NULL:
            zstructFree(self.recordSize)
            self.recordSize=NULL

cpdef list pd_size(Open fid,char *pathname):
    cdef:
        dss_info info 
        int curve_no,data_no,data_type,label_size

    info = dss_info(fid,pathname)
    curve_no = info.pd_curve_no
    label_size = int((info.pdLabelsLength - curve_no)/curve_no*1.0)
    data_no = info.pd_data_no
    data_type =info.dataType
    if data_type == 200:
        dtype = 'float32'
    elif data_type == 205:
        dtype = 'double'
    else:
        dtype = 'unknown'
    
    return_list = [curve_no,data_no,data_type,dtype,label_size]
    return return_list 

cpdef squeeze_file(str file_path):
    cdef int status
    status = zsqueeze(file_path)

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

    def getParts(self):
        return [self.getAPart(),self.getBPart(),self.getCPart(),self.getDPart(),self.getEPart(),self.getFPart()]
