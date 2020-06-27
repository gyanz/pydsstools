import logging
import numpy as np
import numpy.ma as ma
from ..core import (HecTime, DssStatusException, GranularityException,ArgumentException,DssLastError,setMessageLevel,squeeze_file) 
from ..core import (GRID_TYPE, GRID_DATA_TYPE, GRID_COMPRESSION_METHODS,gridInfo,gridDataSource)
from ..core import Open as _Open
from ..core import UNDEFINED
import atexit
        
__all__ = ['dss_logging','HecTime', 'DssStatusException', 'GranularityException', 'ArgumentException', 'DssLastError','gridInfo','gridDataSource','computeGridStats','grid_type_names','grid_data_type_names','UNDEFINED']

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

def computeGridStats(data,compute_range = True):
    """ Compute statistical value for numpy array data for Spatial grid

    Parameter
    ---------
        # data: numpy array or masked array
        # compute_range: boolean, string or list of values
            # boolean - True, False
            # string - quartiles, quarters, TODO
            # list/tuple - list of values (max 19 excluding nodata) to compute equal to greater than cell counts
    """
    result = {'min': None, 'max': None, 'mean': None,'range_values':[], 'range_counts': []}
    total_cells = data.size

    if total_cells == 0:
        logging.info('Empty Grid Array!')
        return

    if isinstance(data,ma.core.MaskedArray):
        data = data[~data.mask]
        data = data._data
    elif isinstance(data,np.ndarray):
        data = data[~np.isnan(data)]
    else:
        raise Exception('Invalid data. Numpy or Masked Array expected.')

    min_value = data.min()
    max_value = data.max()
    mean_value = data.mean()

    result.update([('min',min_value),('max',max_value),('mean',mean_value)])
    #print(result)

    range_values = []
    if isinstance(compute_range,(list,tuple)):
        range_values = sorted([x for x in compute_range if not (np.isnan(x) or x < min_value or x > max_value)])
        
    elif compute_range or isinstance(compute_range,str):
        # default range
        if min_value < 0 and max_value > 0:
            range_values = np.linspace(min_value,max_value,10)
            range_values = range_values.tolist()
        else:
            q0 = min_value
            q1 = 0.25 * (min_value + max_value)
            q2 = 0.5 * (min_value + max_value)
            q3 = 0.75 * (min_value + max_value)
            range_values = [q0,q1,q2,q3]
        range_values = [round(x,2) for x in range_values]
    else:
        pass

    range_values = range_values[0:19]
    range_values.insert(0,np.nan)
    range_counts = [total_cells] # assuming no data is very small negative number
    #print(type(data),'data=',data,'\n')
    #print(range_values,range_counts)
    for val in range_values[1:]:
        count = (data >= val).sum()
        range_counts.append(count)
    
    result.update([('range_values',range_values),('range_counts',range_counts)])
    return result

grid_data_type_names = tuple(GRID_DATA_TYPE.keys())
grid_type_names = tuple(GRID_TYPE.keys())
