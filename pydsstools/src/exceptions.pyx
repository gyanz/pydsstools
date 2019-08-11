cdef int STATUS_OK= 0 #0 or greater for no error 
cdef int STATUS_NOT_OKAY = -1 # negative integer for error, severity greater with larger negative code??
cdef int STATUS_RECORD_NOT_FOUND = -1

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
        
    def __cinit__(self,*args,**kwargs):
        self.err= <hec_zdssLastError *>PyMem_Malloc(sizeof(hec_zdssLastError))
        if not self.err:
            raise MemoryError()
        zerror(self.err)
        
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
    # TODO: Improve this
    cdef:
        DssLastError err_obj

    err_obj = DssLastError()
    if err_obj.errorCode != 0:
        if not err_obj.errorType == 1: 
            # type other than warning
            raise DssStatusException(status,err_obj.errorMessage)
        logging.warn('%s',err_obj.errorMessage)
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
    
