import logging
import numpy as np
import numpy.ma as ma
import math
from .._lib import BoundingBox
from ..core import (HecTime, DssStatusException, GranularityException,ArgumentException,DssLastError,setMessageLevel,squeeze_file) 
from ..core import (GRID_TYPE, GRID_DATA_TYPE, GRID_COMPRESSION_METHODS,gridInfo)
from ..core import (check_shg_gridinfo,correct_shg_gridinfo,lower_left_xy_from_transform)
from ..core import Open as _Open
from ..core import UNDEFINED
import atexit
from affine import Affine        

__all__ = ['dss_logging','HecTime', 'DssStatusException', 'GranularityException', 'ArgumentException', 'DssLastError','gridInfo','computeGridStats','grid_type_names','grid_data_type_names','UNDEFINED','HRAP_WKT','SHG_WKT','check_gridinfo','BoundingBox','check_shg_gridinfo','correct_shg_gridinfo','lower_left_xy_from_transform']

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

grid_data_type_names = tuple(GRID_DATA_TYPE.keys())
grid_type_names = tuple(GRID_TYPE.keys())

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

def check_gridinfo(grid_info,shape,raise_error = False):
    """ Checks the grid meta data for consistency and corrects values where necessary

    Parameter
    ---------
        grid_info: dict or gridInfo instance

    """
    grid_info = grid_info.copy()
    default_gridinfo = gridInfo()
    required_params = [x for x in default_gridinfo if not x.startswith('opt')]
    opt_params = [x for x in default_gridinfo if x.startswith('opt')]

    for k in required_params:
        if not k in grid_info:
            raise Exception('%s grid info parameter not provided'%k)

    for k in opt_params:
        if not k in grid_info:
            grid_info[k] = default_gridinfo[k]

    grid_type = grid_info['grid_type']
    if not grid_type in grid_type_names:
        raise Exception('grid_type must be one of %r'%grid_type_names) 

    if grid_type in ['hrap','hrap-time']:
        logging.debug('WKT CRS for HRAP grid applied')
        grid_info['grid_crs'] = HRAP_WKT
        grid_info['opt_crs_name'] = 'HRAP'

    if grid_type in ['shg','shg-time']:
        logging.debug('WKT CRS for SHG grid applied')
        grid_info['grid_crs'] = SHG_WKT
        grid_info['opt_crs_name'] = 'SHG'

    if grid_type in ['albers','albers-time']:
        logging.debug('WKT CRS for SHG grid applied')
        grid_info['grid_crs'] = SHG_WKT
        grid_info['opt_crs_name'] = 'AlbersInfo'

    transform = grid_info['grid_transform']
    if not isinstance(transform, Affine):
        raise Exception('grid_transform must be Affine instance') 

    grid_crs = grid_info['grid_crs']
    if not isinstance(grid_crs, str):
        raise Exception('grid coordinate reference must be string type') 

    data_type = grid_info['data_type']
    if not data_type in grid_data_type_names:
        raise Exception('data_type must be one of %r'%grid_data_type_names) 

    opt_data_source = grid_info['opt_data_source']
    # I don't know much about this parameter other than it must be char or string type
    if not isinstance(opt_data_source,str):
        logging.debug('Empty data source string used')
        opt_data_source = ''

    grid_info['opt_data_source'] = opt_data_source

    if grid_type in ['hrap','hrap-time'] and not opt_data_source:
        logging.warn('Invalid data source for HRAP grid provided')

    if not isinstance(grid_info['opt_tzid'],str):
        logging.debug('Empty time zone id string used')
        grid_info['opt_tzid'] = ''

    if not isinstance(grid_info['opt_tzoffset'],int):
        logging.debug('time offset of 0 used')
        grid_info['opt_tzoffset'] = 0

    if not isinstance(grid_info['opt_crs_name'],str):
        grid_info['opt_crs_name'] = 'UNDEFINED'

    if not isinstance(grid_info['opt_crs_type'],int):
        grid_info['opt_crs_type'] = 0 # = WKT

    if not grid_info['opt_crs_type'] in (0,1,2):
        # 0 = WKT, 1 = PROJ4, 2 = GML
        msg = 'Invalid opt_crs_type value %s used'%(grid_info['opt_crs_type'])
        logging.error(msg)
        if raise_error:
            raise Exception(msg)
        grid_info['opt_crs_type'] = 0 # defaults to WKT if error not raised

    if grid_info['opt_is_interval']:
        grid_info['opt_is_interval'] = 1
    else:
        grid_info['opt_is_interval'] = 0

    if grid_info['opt_time_stamped']:
        grid_info['opt_time_stamped'] = 1
    else:
        grid_info['opt_time_stamped'] = 0

    # check lower_left_x and lower_left_y indices
    ll_x1 = grid_info['opt_lower_left_x']
    ll_y1 = grid_info['opt_lower_left_y']
    cell_zero_xcoord = grid_info['opt_cell_zero_xcoord']
    cell_zero_ycoord = grid_info['opt_cell_zero_ycoord']
    ll_x2, ll_y2 = lower_left_xy_from_transform(transform,shape,cell_zero_xcoord,cell_zero_ycoord)
    if ll_x1 != ll_x2 or ll_y1 != ll_y2:
        msg = 'opt_lower_left_x, opt_lower_left_y has issue or both are incorrect\n'
        msg += 'Given = %r, computed = %r'%((ll_x1,ll_y1), (ll_x2, ll_y2))
        logging.error(msg)
        if raise_error:
            raise Exception(msg)

    # check time stamped vs grid_type and pathname D and F parts in put_grid  

    return grid_info
