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
            raise BaseException(f"The queried dss record is either invalid or does not exist: {pathname}.")

        # ALL
        self.dataType = self.recordSize[0].dataType
        logging.debug(f"RecordSize: data type = {self.dataType}.")
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
    if not (info.dataType >= 200 and info.dataType <=205):
        raise TypeError(f"Problem with paired data information querry. The provided dss record is not paired data type: {pathname}.")

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

cdef class DssPathName:
    cdef:
        dict _parts

    def __init__(self,pathname):
        self._parts = DssPathName._parse(pathname)

    @staticmethod
    def _parse(pathname):
        if isinstance(pathname,str):
            parts = pathname.split('/')[1:-1]    
            if not len(parts) == 6:
                logging.error('Invalid dss pathname: No of pathname parts not equal to six')
                raise DssPathException('Invalid dss pathname: No of pathname parts not equal to six')

            return dict(zip(("A","B","C","D","E","F"),parts))
        
        elif isinstance(pathname,DssPathName):
            return pathname._parts.copy()
        
        else:
            raise TypeError(f"Expected string or DssPathname, got {type(pathname).__name__}")

    def __repr__(self):
        return self.text()

    def text(self):
        txt = "/"
        for _,part in self._parts.items():
            txt += part + "/"
        return txt
    
    @property
    def str(self):
        return self.text()
    
    @property
    def apart(self):
        return self._parts["A"]

    @apart.setter
    def apart(self,val):
        self._parts["A"] = val

    @property
    def bpart(self):
        return self._parts["B"]

    @bpart.setter
    def bpart(self,val):
        self._parts["B"] = val

    @property
    def cpart(self):
        return self._parts["C"]

    @cpart.setter
    def cpart(self,val):
        self._parts["C"] = val

    @property
    def dpart(self):
        return self._parts["D"]

    @dpart.setter
    def dpart(self,val):
        self._parts["D"] = val

    @property
    def epart(self):
        return self._parts["E"]

    @epart.setter
    def epart(self,val):
        self._parts["E"] = val

    @property
    def fpart(self):
        return self._parts["F"]

    @fpart.setter
    def fpart(self,val):
        self._parts["F"] = val

    @property
    def parts(self):
        return list(self._parts.values())

    def epart_to_interval(self,dss_ver=7):
        return DssPathName._epart_operations(self.epart, dss_ver, opt = 1) 

    @staticmethod
    def interval_to_epart(int interval, dss_ver=7):
        return DssPathName._epart_operations(interval, dss_ver, opt = 2) 

    @staticmethod
    def _epart_operations(object data, int dss_ver=7, int opt=0):
        # TODO: return interval in seconds for dss = 7
        cdef:
            #char* _epart
            bytearray epart
            unsigned char[:] epart_view
            size_t _size_epart
            Py_ssize_t n        
            str epart_revised
            int _interval
            int interval
            int _opt
            int status

        if opt < 0 or opt > 2:
            raise ValueError(f"Operation code '{opt}' is out of range.")

        _opt = <int>opt 
        
        if opt == 0:
            # Epart to interval seconds and fixed Epart
            epart = bytearray(25)
            n = len(epart)
            epart[:n] = data.encode("ascii")
            epart_view = epart
            _size_epart = n
            status = ztsGetStandardInterval(dss_ver, &_interval, <char*>&epart_view[0], _size_epart, &_opt)
            if status == nok:
                return None
            n = strlen(<char*>&epart_view[0])
            epart_revised = bytes(epart[:n]).decode("ascii")
            return (_interval,epart_revised)

        elif opt == 1:
            # Epart to interval seconds    
            epart = bytearray(25)
            n = len(epart)
            epart[:n] = data.encode("ascii")
            epart_view = epart
            _size_epart = n
            status = ztsGetStandardInterval(dss_ver, &_interval, <char*>&epart_view[0], _size_epart, &_opt)
            if status == nok:
                return None
            return _interval

        #elif opt == 2:
        else:
            # interval seconds to Epart
            epart = bytearray(25)
            _size_epart = len(epart)
            epart_view = epart
            interval = int(data)
            _interval = <int>interval    
            status = ztsGetStandardInterval(dss_ver, &_interval, <char*>&epart_view[0], _size_epart, &_opt)
            if status == nok:
                return None
            n = strlen(<char*>&epart_view[0])
            epart_revised = bytes(epart[:n]).decode("ascii")
            return epart_revised

        
