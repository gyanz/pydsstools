from pydsstools import _heclib
from ctypes import c_int

STATUS_OK=0 # 0 or greater for no error 
STATUS_NOT_OKAY = -1 # negative integer for error, severity greater with larger negative code??
STATUS_RECORD_NOT_FOUND = -1

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

_gzisError = getattr(_heclib,"gzisError")
_gzisError.argtypes=(c_int,)
_gzisError.restype = c_int

_gzerrorSeverity = getattr(_heclib,"gzerrorSeverity")
_gzerrorSeverity.argtypes=(c_int,)
_gzerrorSeverity.restype = c_int

class DssStatusException(Exception):
    def __init__(self,status,message=None):
        super().__init__(status,message)
        self.message=message
        self.status=status

def isError(status):
    print("Return status = {}\n".format(status))
    if not status == STATUS_OK:
        _true = _gzisError(status) # check if it actually an error
        if _true:
            print("isError: zisError return = {}".format(_true))
            _err_code = _gzerrorSeverity(status) # get the severity of error
            raise DssStatusException(status,ErrorSeverityCodes[_err_code])

    if status == STATUS_RECORD_NOT_FOUND:
        print("isError: Path record probably does not exist")
         # need other checks??

    return None 

class GranularityException(Exception):
    def __init__(self,granularity_value,message,):
        super().__init__(granularity_value,message)
        self.message=message
        self.granularity_value=granularity_value

class ArgumentException(Exception):
    pass

