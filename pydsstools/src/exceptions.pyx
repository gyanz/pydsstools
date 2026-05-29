# HEC-DSS C error API reference
#
# zerrorCheck()
#     Return the severity of the most recent saved HEC-DSS error.
#
#     Returns 0 when no error is currently saved, otherwise returns the saved
#     error severity. This is a quick global check and does not provide error
#     details.
#
# zerror(errorStruct)
#     Copy the most recent saved HEC-DSS error into ``errorStruct``.
#
#     Returns the saved error severity. Use this after a DSS call fails when
#     detailed diagnostics are needed, such as the encoded error code, DSS error
#     number, system error, function ID, error message, pathname, and filename.
#
# zerrorSeverity(errorCode)
#     Decode and return the severity component of an encoded HEC-DSS error code.
#
#     This operates only on the ``errorCode`` argument. It does not inspect the
#     saved global last-error state.
#
# zisError(status)
#     Return true when a DSS status code represents an actual error.
#
#     Status values greater than or equal to 0 are not errors. Record-not-found
#     status is also not treated as an error. Encoded DSS error codes are decoded
#     and treated as errors only when their severity is at least
#     ``INVALID_ARGUMENT``.

#cdef int STATUS_OK= 0 #0 or greater for no error
#cdef int STATUS_NOT_OKAY = -1 # negative integer for error, severity greater with larger negative code??
#cdef int STATUS_RECORD_NOT_FOUND = -1
cdef int ok = STATUS_OKAY
cdef int nok = STATUS_NOT_OKAY
cdef int rfound = STATUS_RECORD_FOUND
cdef int rnfound = STATUS_RECORD_NOT_FOUND

# Error Severity Check

ErrorSeverityCodes= {1: "INFORMATION",
                    2: "WARNING",
                    3: "WARNING_NO_WRITE",
                    4: "WARNING_NO_FILE_ACCESS",
                    5: "WRITE_ERROR",
                    6: "READ_ERROR",
                    7: "CORRUP_FILE",
                    8: "MEMORY_ERROR",
                    9: "CRITICAL_ERROR"}

ErrorTypes = {0: "None",
              1: "WARNING",
              2: "ACCESS",
              3: "FILE",
              4: "MEMORY"}

@cython.freelist(2)
cdef class DssLastError:
    cdef:
        hec_zdssLastError *err
        int status
        
    def __cinit__(self,*args,**kwargs):
        logger.debug('Initialization of DssLastError')
        self.err= <hec_zdssLastError *>PyMem_Malloc(sizeof(hec_zdssLastError))
        if not self.err:
            raise MemoryError()
        # zerror simply copies the static hec_zdssLastError into err
        # zerrorCheck returns err.severity
        # zerrorStructClear resets err
        self.status = zerror(self.err)
        
    property errorCode:
        def __get__(self):
            return self.err[0].errorCode
            
    property errorNumber:
        def __get__(self):
            return self.err[0].errorNumber
            
    property errorType:
        def __get__(self):
            return self.err[0].errorType
            
    property severity:
        def __get__(self):
            return self.err[0].severity
            
    property systemError:
        def __get__(self):
            return self.err[0].systemError

    property errorMessage:
        def __get__(self):
            return self.err[0].errorMessage

    property systemErrorMessage:
        def __get__(self):
            return self.err[0].systemErrorMessage            

    property lastPathname:
        def __get__(self):
            return self.err[0].lastPathname
         
    property filename:
        def __get__(self):
            return self.err[0].filename
            
    def __dealloc__(self):
        PyMem_Free(self.err)

class DssStatusException(Exception):
    def __init__(self,status,message=None):
        super().__init__(status,message)
        self.message=message
        self.status=status

def isError(int status):
    # TODO: Not working as expected, not useful for DSS v6
    cdef:
        DssLastError err_obj

    err_obj = DssLastError()
    logger.debug(f"dss check: Open status = {status}, zerror status = {err_obj.status}, error code = {err_obj.errorCode}, error type = {err_obj.errorType}, message = {err_obj.errorMessage}.")
    if err_obj.errorCode != 0:
        if not err_obj.errorType == 1: 
            # type other than warning
            raise DssStatusException(status,err_obj.errorMessage)
        logger.warning('%s',err_obj.errorMessage)

    if status == nok:
        raise DssStatusException(status,f'Error code {status} returned by HEC-DSS function call. Either record does not exist or another error may have occured.')    

    if status == -123:
        # Line 43 in hec-dss/heclib/heclib_c/src/DssInterface/v6and7/zopen.c
        logger.error(f'Error code {status} returned by HEC-DSS open call. DSS 6 is not supported in Linux and Mac OS.')    
        raise DssStatusException(status,f'DSS6 not supported in Mac and Linux')    

    return status


class GranularityException(Exception):
    def __init__(self,granularity_value,message):
        super().__init__(granularity_value,message)
        self.message=message
        self.granularity_value=granularity_value

class ArgumentException(Exception):
    pass


class DssPathException(BaseException):
    def __init__(self,msg):
        self.msg = msg

    def __repr__(self):
        return self.msg


# ---------------------------------------------------------------------------
# DSS-6 Fortran istat checker
# ---------------------------------------------------------------------------

_DSS6_ISTAT_MSG = {
    1:   "some data values are missing sentinels (-901)",
    2:   "some requested time blocks not found, partial data returned",
    3:   "missing time blocks and missing value sentinels",
    4:   "no data returned / all values missing",
    5:   "pathname not found in file",
    11:  "number of values < 1 (illegal call)",
    12:  "non-standard or missing time interval",
    15:  "illegal starting date or time",
    16:  "insufficient internal memory",
    20:  "record is not the expected time-series type",
    21:  "buffer size not large enough",
    24:  "pathname not recognised as expected record type",
    30:  "file is opened read-only",
    51:  "illegal data compression scheme",
    52:  "illegal data compression precision value",
    511: "record type mismatch with existing record in file",
}

# Non-fatal istat codes per function, mapped to the logging function to use.
# Any non-zero code absent from a function's entry raises RuntimeError.
_DSS6_FUNC_LENIENCY = {
    # Read regular TS: 1=missing sentinels, 2=missing blocks, 3=both, 4=no data.
    # All are non-fatal because the location header is populated before Fortran
    # returns any of these codes, so the header fields are valid.
    "zrrtsc_": {1: logging.debug, 2: logging.debug,
                3: logging.debug, 4: logging.debug},
    # Read irregular TS: 1=nvals exceeded kvals (data truncated, header ok),
    # 3=no values in window (header still populated), 4=block not found.
    "zritsc_": {1: logging.debug, 3: logging.debug, 4: logging.debug},
    # Write regular TS: 4=all values missing, record may not be stored.
    "zsrtsc_": {4: logging.warning},
    # Write irregular TS: 4=nvals=0, nothing was written.
    "zsitsc_": {4: logging.warning},
}

def _check_dss6_istat(istat, func, pathname):
    """Check a DSS-6 Fortran istat return code.

    istat=0 returns silently.  Non-zero codes in _DSS6_FUNC_LENIENCY for
    the given func are logged at the registered level and then return
    normally.  Any other non-zero code raises RuntimeError.
    """
    if istat == 0:
        return
    msg = _DSS6_ISTAT_MSG.get(istat, f"unknown status code {istat}")
    text = f"{func} istat={istat} ({msg}) for {pathname!r}"
    log_fn = _DSS6_FUNC_LENIENCY.get(func, {}).get(istat)
    if log_fn is not None:
        log_fn(text)
    else:
        raise RuntimeError(text)

