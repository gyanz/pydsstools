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
        logging.debug('Initialization of DssLastError')
        self.err= <hec_zdssLastError *>PyMem_Malloc(sizeof(hec_zdssLastError))
        if not self.err:
            raise MemoryError()
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
    # TODO: Not working as expected
    cdef:
        DssLastError err_obj

    err_obj = DssLastError()
    logging.debug(f"dss check: Open status = {status}, zerror status = {err_obj.status}, error code = {err_obj.errorCode}, error type = {err_obj.errorType}, message = {err_obj.errorMessage}.")
    if err_obj.errorCode != 0:
        if not err_obj.errorType == 1: 
            # type other than warning
            raise DssStatusException(status,err_obj.errorMessage)
        logging.warn('%s',err_obj.errorMessage)

    if status == nok:
        raise DssStatusException(status,f'Error code {status} returned by HEC-DSS function call. Either record does not exist or another error may have occured.')    

    if status == -123:
        # Line 43 in hec-dss/heclib/heclib_c/src/DssInterface/v6and7/zopen.c
        logging.error(f'Error code {status} returned by HEC-DSS open call. DSS 6 is not supported in Linux and Mac OS.')    
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
    
