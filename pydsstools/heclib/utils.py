import logging
from ..core import (HecTime, DssStatusException, GranularityException,ArgumentException,DssLastError,setMessageLevel,squeeze_file)
from ..core import Open as _Open
import atexit
        
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

__dsslog = None

@atexit.register
def __close():
    if not __dsslog is None:
        try:
            __dsslog.close()
        except:
            logging.error('Error closing dsslog')
        else:
            logging.debug('dsslog file closed')

def __init():
    global __dsslog
    if not __dsslog is None:
        from os import path
        dss_file = path.join(path.dirname(__file__),dsslog.dss)
        logging.info('File used to intialize pydsstools messaging is %s',dss_file)
        __dsslog = _Open(dss_file)

__init()

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
        setMessagelevel(0,level)

    def config(self,method=0,level='General'):
        if method in log_method:
            if level in log_level:
                pass
            elif level in _log_level:
                level = _log_level[level]
            else:
                logging.warn('Invalid Dss Logging Level ignored')
                return
            logging.warn('***Setting DSS Logging, Method = %r, Level = %r***', method, level)
            setMessageLevel(method,level)
        else:
            logging.warn('Invalid Dss Logging Method ignored')

dss_logging = DssLogging()
