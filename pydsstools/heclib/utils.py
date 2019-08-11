import logging
from ..core import (HecTime, DssStatusException, GranularityException,ArgumentException,DssLastError,setMessageLevel)

__all__ = ['dss_logging','HecTime', 'DssStatusException', 'GranularityException', 'ArgumentException', 'DssLastError']

log_level = {0: 'None',
             1: 'Error',
             2: 'Critical',
             3: 'General',
             4: 'Info',
             5: 'Debug',
             6: 'Diagnostic'}

_log_level = dict(zip(log_level.values(),log_level.keys()))

log_method =  {0:  'ALL',
               1:  'VER7',
               2:  'READ_LOWLEVEL',
               3:  'WRITE_LOWLEVEL',
               4:  'READ',
               5:  'WRITE',
               6:  '_',
               7:  'OPEN',
               8:  'CHECK_RECORD',
               9:  'LOCKING',
              10: 'READ_TS',
              11: 'WRITE_TS',
              12: 'ALIAS',
              13: 'COPY',
              14: 'UTILITY',
              15: 'CATALOG',
              16: 'FILE_INTEGRITY'}

class DssLogging(object):
    def setLevel(self,level):
        if level in log_level:
            pass
        elif level in _log_level:
            level = _log_level[level]
        else:
            logging.warn('Invalid Dss Logging Level ignored')
            return

        logging.warn('***Setting DSS Logging***')
        setMessagelevel(1,level)

    def config(self,method,level):
        if method in log_method:
            if level in log_level:
                pass
            elif level in _log_level:
                level = _log_level[level]
            else:
                logging.warn('Invalid Dss Logging Level ignored')
                return
            logging.warn('***Setting DSS Logging***')
            setMessageLevel(method,level)
        else:
            logging.warn('Invalid Dss Logging Method ignored')

dss_logging = DssLogging()
