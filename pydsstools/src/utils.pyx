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

cpdef int copy_record_to(Open copyFrom, str copyToFile, str pathnameFrom, str pathnameTo):

'''
def str2ascii(file):
    if isinstance(file,str):
        return file.encode('ascii')
    elif isinstance(file,bytes):
        return file
    else:
        logger.error("Wrong filename or encoding (not ascii or byte) ")

cpdef void set_message_level(int methodID,int levelID):
    zsetMessageLevel(methodID, levelID)

cpdef int get_message_level(int methodID):
    return zgetMessageLevel(methodID)

cpdef void set_program_name(str name):
    cdef bytes bname = name[:16].encode('ascii')
    zset(b"program", bname, 0)

HeclibVersion = _namedtuple('HeclibVersion', ['version', 'date'])

cpdef object heclib_version():
    cdef char ver[32]
    cdef char date[32]
    cdef int ival
    zquery(b"version", ver, sizeof(ver), &ival)
    zquery(b"date", date, sizeof(date), &ival)
    return HeclibVersion(ver, date)

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
        logger.debug(f"RecordSize: data type = {self.dataType}.")
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

cpdef int copy_record_to(Open copyFrom, str copyToFile, str pathnameFrom, str pathnameTo):
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

cpdef int copy_file(Open src, Open dst, int status_wanted=0):
    """Copy (merge) records from one open DSS file into another open DSS file.

    Wraps ``zcopyFile``.  Uses a brute-force byte scan of the source file, so
    it can recover records from a damaged file that is otherwise unreadable via
    normal catalog/index access.  Cross-version copies (DSS-6 ↔ DSS-7) are
    handled transparently.

    Behaviour when a record already exists in *dst*
    ------------------------------------------------
    There is no skip-if-exists option at the C level.  Every record that
    matches *status_wanted* is always written:

    - **Time series** – values are *merged* with what is already in *dst* at
      the same pathname (blocks are appended / overlapping blocks replaced).
    - **All other types** (paired data, grid, array, text, binary) – the
      existing *dst* record is *replaced* entirely.

    Parameters
    ----------
    src : Open
        Source DSS file handle (already open).
    dst : Open
        Destination DSS file handle (already open).
    status_wanted : int or CopyRecordFlag
        Selects which records to copy.  Accepts plain ``int`` or a
        ``CopyRecordFlag`` enum member (both are equivalent)::

            CopyRecordFlag.valid   = 0   all valid records (default)
            CopyRecordFlag.primary = 1   primary records only
            CopyRecordFlag.alias   = 2   alias records only
            CopyRecordFlag.deleted = 11  soft-deleted records only
            CopyRecordFlag.renamed = 12  renamed-tombstone records only
            CopyRecordFlag.any     = 100 every record, regardless of status

    Returns
    -------
    int
        0 (STATUS_OKAY) on success, negative DSS error code on failure.
    """
    cdef:
        long long *ifltabFrom = src.ifltab
        long long *ifltabTo = dst.ifltab
        int status
    status = zcopyFile(ifltabFrom, ifltabTo, status_wanted)
    return status

cpdef int copy_file_to(Open src, str dst_path, int status_wanted=0):
    """Copy (merge) records from an open DSS file into a DSS file at *dst_path*.

    Convenience wrapper around ``copy_file``: opens *dst_path* automatically,
    performs the copy, then closes it.  See ``copy_file`` for full behaviour
    details including cross-version support and existing-record semantics.

    Parameters
    ----------
    src : Open
        Source DSS file handle (already open).
    dst_path : str
        Path of the destination DSS file.  Created if it does not exist;
        otherwise opened and records are merged in.
    status_wanted : int or CopyRecordFlag
        Selects which records to copy (default 0 = all valid).
        See ``CopyRecordFlag`` for the full set of values.

    Returns
    -------
    int
        0 (STATUS_OKAY) on success, negative DSS error code on failure.
    """
    cdef:
        long long *ifltabFrom = src.ifltab
        long long *ifltabTo = NULL
        Open fid
        int status
    with Open(dst_path) as fid:
        ifltabTo = fid.ifltab
        status = zcopyFile(ifltabFrom, ifltabTo, status_wanted)
    return status

cpdef int convert_version(str src_path, str dst_path):
    """Convert a DSS file between version 6 and version 7.

    Wraps ``zconvertVersion``.  Detects the source version automatically and
    creates (or opens) *dst_path* with the opposite version, then copies all
    records via ``zcopyFile``.

    Destination file rules (enforced by the C library)
    ---------------------------------------------------
    +--------------------------+----------------------------------------------+
    | *dst_path* state         | behaviour                                    |
    +==========================+==============================================+
    | does not exist           | created with the opposite version, then      |
    |                          | populated — the normal case                  |
    +--------------------------+----------------------------------------------+
    | exists, same version     | returns a negative ``FILE_EXISTS`` error;    |
    | as *src_path*            | use the *force* option on ``HecDss.Open``   |
    |                          | ``.convert_version()`` to remove it first    |
    +--------------------------+----------------------------------------------+
    | exists, different        | opened and records are merged in             |
    | version from *src_path*  |                                              |
    +--------------------------+----------------------------------------------+

    Parameters
    ----------
    src_path : str
        Path to the source DSS file (must exist; may be open elsewhere).
    dst_path : str
        Path for the output file.  Should not exist when converting to a
        fresh file; see table above for existing-file behaviour.

    Returns
    -------
    int
        0 (STATUS_OKAY) on success, negative DSS error code on failure.
    """
    cdef int status
    status = zconvertVersion(src_path, dst_path)
    return status

cpdef int check_file(Open fid):
    """Run a thorough integrity check on an open DSS file.

    Wraps ``zcheckFile``.  Runs each sub-check in sequence and returns on the
    first failure, so the count reflects errors from that sub-check only:

    - **DSS-6**: checks page/node blocks (``zckpnb6``), links (``zcklnk6``),
      and pathname tables (``zckpat6``).
    - **DSS-7**: checks links (``zcheckLinks``), pathname tables
      (``zcheckPathnames``), pathname bins (``zcheckPathnameBins``), and the
      hash table (``zcheckHashTable``).

    This is the most resource-intensive function in the DSS library; use it
    for diagnostics and file-recovery workflows, not routine access.

    Parameters
    ----------
    fid : Open
        DSS file handle (already open).

    Returns
    -------
    int
        * ``0``   – file is clean (STATUS_OKAY)
        * ``> 0`` – error count from the first failing sub-check
          (subsequent sub-checks are not run)
        * ``< 0`` – negative DSS error code indicating a severe /
          unrecoverable error
    """
    cdef:
        long long *ifltab = fid.ifltab
        int status
    status = zcheckFile(ifltab)
    return status

cpdef int delete_pathname(Open fid, str pathname):
    cdef:
        long long *ifltab = fid.ifltab
        const char *path_name = pathname
        int status
    status = zdelete(ifltab, path_name)
    return status

cpdef int rename_pathname(Open fid, str old_pathname, str new_pathname):
    cdef:
        long long *ifltab = fid.ifltab
        const char *old_path = old_pathname
        const char *new_path = new_pathname
        int status
    status = zrename(ifltab, old_path, new_path)
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
        readonly dict _parts

    def __init__(self,pathname):
        self._parts = DssPathName._parse(pathname)

    @staticmethod
    def _parse(pathname):
        if isinstance(pathname,str):
            parts = pathname.split('/')[1:-1]    
            if not len(parts) == 6:
                logger.error('Invalid dss pathname: No of pathname parts not equal to six')
                raise DssPathException('Invalid dss pathname: No of pathname parts not equal to six')

            return dict(zip(("A","B","C","D","E","F"),parts))
        
        elif isinstance(pathname,DssPathName):
            return pathname._parts.copy()
        
        else:
            raise TypeError(f"Expected string or DssPathname, got {type(pathname).__name__}")

    def __repr__(self):
        return self.text()

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                other = DssPathName(other)
            except DssPathException:
                return NotImplemented
        elif not isinstance(other, DssPathName):
            return NotImplemented
        return self.text().lower() == other.text().lower()

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

    def normalize_period(self, date_style=104, time_style=0):
        """Correct d-part and e-part datetime strings for gridded DSS data.

        For gridded (time-stamped) records the d-part must express midnight as
        00:00 of the current day (midnight_as_2400=False) and the e-part must
        express midnight as 24:00 of the *previous* day (midnight_as_2400=True).
        Each part is normalized independently in a new DssPathName object; the
        original is not modified. An empty e-part (instantaneous grid) is left
        unchanged. If a part cannot be parsed a warning is logged and that part
        is left unchanged.

        Parameters
        ----------
        date_style : int, optional
            Date formatting style code passed to HecTime (see HecTime._date_style_codes()).
            Default is 104 (``02JAN2025`` style).
        time_style : int, optional
            Time formatting style code passed to HecTime.
            0: ``0830``, 1: ``08:30``, 2: ``08:30:00``. Default is 0.

        Returns
        -------
        DssPathName
            New instance with corrected d-part and/or e-part.

        Examples
        --------
        >>> path = DssPathName("/A/B/C/01JAN2025:2300/02JAN2025:0000/F/")
        >>> fixed = path.normalize_period()
        >>> fixed.dpart
        '01JAN2025:2300'
        >>> fixed.epart
        '01JAN2025:2400'
        """
        new_path = DssPathName(self)
        try:
            stime = HecTime(self.dpart, midnight_as_2400=False, date_style=date_style, time_style=time_style)
            new_path.dpart = stime.text()
        except Exception as e:
            logger.warning(f"normalize_period: could not parse d-part datetime: {e}")
        if self.epart.strip():
            try:
                etime = HecTime(self.epart, midnight_as_2400=True, date_style=date_style, time_style=time_style)
                new_path.epart = etime.text()
            except Exception as e:
                logger.warning(f"normalize_period: could not parse e-part datetime: {e}")
        return new_path

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

        
