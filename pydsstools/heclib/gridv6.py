'''
This module provides data structures and methods for interacting with DSS 6 grids. 
Since the implementation in this file is subject to change, direct use of this module is not recommended.
* Use pydsstools.heclib.dss.Heclib.Open.put_grid6 to write grid to dss 6 file.
* Currently grid data is read from dss file using read_grid method. DSS 6 grid is read and converted to DSS 7 form using C++ code.
* TODO: provide read_grid6 method to get DSS 6 grid in native format. 
'''
import logging
import struct
import ctypes
import math
import numpy as np
from pyproj import CRS
from ..core import HecTime,DssPathName
from ..core import HRAP_WKT, SHG_WKT as SHG_WKT_DEFAULT
from ..core import GRID_TYPE, GRID_DATA_TYPE, GRID_COMPRESSION_METHODS 
from ..core import UNDEFINED, NODATA_TIME, NODATA_NEGATIVE

__all__ = ['GridHrapInfo','GridAlbersInfo','GridSpecifiedInfo']

NODATA_FLOAT = UNDEFINED
GRID_NODATA_VALUE = NODATA_FLOAT
NODATA_INT = NODATA_NEGATIVE
# following are consistent with HECDSS7, GRID_COMPRESSION_METHOD
# not using GRID_COMPRESSION_METHOD as HECDSS7 constants may change in future
PRECIP_2_BYTE = 101001
UNDEFINED_COMPRESSION = 0
NO_COMPRESSION = 1
ZLIB_DEFLATE_COMPRESSION = 26
#
UNDEFINED_PROJECTION_DATUM = 0
NAD_27 = 1
NAD_83 = 2
#
DSS7_GRID_STRUCT_VERSION = 100
GRID_STRUCT_VERSION_UNDEFINED = -1
GRIDINFO_VERSION = 1
# It looks like GridInfo Version in DSSVue is either 2 (Specified grid) or 1 (other grids)
# Only Specified GridInfo has _version parameter which is set to 2 in pydsstools
# GridInfo shows up as 1 for other grids even though this parameter is not set in pydsstools
SPECIFIED_GRID_INFO_VERSION = 2
#
# GRID_TYPE = {'hrap-time':410, ...}
GRID_TYPE2 = {v:k for k,v in GRID_TYPE.items()}
# GRID_DATA_TYPE = {'per-aver':0, ...}
GRID_DATA_TYPE2 = {v:k for k,v in GRID_DATA_TYPE.items()}
#
SHG_WKT_CUSTOM = '''PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",\
GEOGCS[\"GCS_North_American_{0}\",DATUM[\"D_North_American_{0}\",\
SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],\
UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],\
PARAMETER[\"False_Easting\",{1}],PARAMETER[\"False_Northing\",{2}],\
PARAMETER[\"Central_Meridian\",{3}],PARAMETER[\"Standard_Parallel_1\",{4}],\
PARAMETER[\"Standard_Parallel_2\",{5}],PARAMETER[\"Latitude_Of_Origin\",{6}],\
UNIT[\"Meter\",1.0]]'''

def float32_to_int(f):
    b = struct.pack('<f', f)  # 4-byte float (float32), little endian
    return int.from_bytes(b, 'little')

def str_to_ints(s, endian="little", signed = True):
    b = s.encode('ascii')
    length = len(b)
    if length == 0: length = 1 # fill empty string with nulls

    ints = []
    step = 4
    pad = b'\x00'

    for i in range(0, length, step):
        chunk = b[i:i+4]
        chunk += pad * (4 - len(chunk))  # pad to 4 bytes

        if signed:
            if endian == "little":
                val = struct.unpack('<i', chunk)[0]
            else:
                val = struct.unpack('>i', chunk)[0]
        else:
            if endian == "little":
                val = struct.unpack('<I', chunk)[0]
            else:
                val = struct.unpack('>I', chunk)[0]

        ints.append(val)

    return ints

def str_to_ints_hollerith(s, endian="little", signed = True):
    """
    string formatted as <length>H<text> used on old Fortran
    e.g., 'hello' -> '5Hhello' -> encoded as [ord('5'), ord('H'), ord('h'), ord('e'), ord('l'), ord('l'), ord('o')]
    """
    hollerith = str(len(s)) + 'H' + s
    b = hollerith.encode('ascii')  # convert to bytes

    ints = []
    step = 4
    pad = b'\x00'

    for i in range(0, len(b), step):
        chunk = b[i:i+4]
        chunk += pad * (4 - len(chunk))  # pad to 4 bytes

        if signed:
            if endian == "little":
                val = struct.unpack('<i', chunk)[0]
            else:
                val = struct.unpack('>i', chunk)[0]
        else:
            if endian == "little":
                val = struct.unpack('<I', chunk)[0]
            else:
                val = struct.unpack('>I', chunk)[0]        

        ints.append(val)

    return ints

def ints_to_str(ints, endian="little", signed=True, encoding="ascii",
                strip_trailing_nulls=True, stop_at_first_null=False):
    """
    Convert a list/iterable of 4-byte integers into a string by packing to bytes
    and decoding with the given encoding.

    Parameters
    ----------
    ints : Iterable[int]
        32-bit integers representing raw bytes (4 bytes per int).
    endian : {"little","big"}
        Byte order used when packing each int.
    signed : bool
        Whether ints should be treated as signed (True) or unsigned (False).
    encoding : str
        Text encoding to decode bytes into a Python str (default: "ascii").
    strip_trailing_nulls : bool
        If True, rstrip trailing b"\\x00" after concatenation.
    stop_at_first_null : bool
        If True, truncate at the first NUL byte (C-string style).

    Returns
    -------
    str
        Decoded string.

    Raises
    ------
    UnicodeDecodeError
        If decoding fails under the chosen encoding.
    """
    if signed:
        fmt = '<i' if endian == "little" else '>i'
    else:
        fmt = '<I' if endian == "little" else '>I'

    b = bytearray()
    for val in ints:
        b.extend(struct.pack(fmt, val))

    if stop_at_first_null:
        zero = b.find(0)
        if zero != -1:
            b = b[:zero]

    if strip_trailing_nulls and not stop_at_first_null:
        b = b.rstrip(b'\x00')

    return b.decode(encoding)

def ints_to_str_hollerith(ints, endian="little", signed=True):
    """
    Reverse of str_to_ints_hollerith.
    Takes a list of 4-byte integers, decodes Hollerith (<len>H<text>) back to the original string.
    """
    b = bytearray()

    for val in ints:
        if signed:
            fmt = '<i' if endian == "little" else '>i'
        else:
            fmt = '<I' if endian == "little" else '>I'
        b.extend(struct.pack(fmt, val))

    # Strip any padding nulls at the end
    b = b.rstrip(b'\x00')

    # Decode ASCII
    hollerith_str = b.decode('ascii')

    # Parse Hollerith: format "<length>H<text>"
    # Find the 'H'
    h_pos = hollerith_str.find('H')
    if h_pos == -1:
        raise ValueError("Invalid Hollerith format: missing 'H'")

    length_str = hollerith_str[:h_pos]
    if not length_str.isdigit():
        raise ValueError("Invalid Hollerith format: length not numeric")

    length = int(length_str)
    text = hollerith_str[h_pos+1:]

    if len(text) != length:
        raise ValueError(f"Text length ({len(text)}) does not match Hollerith length ({length})")

    return text

def float32_to_int32(value, endian='<'):
    """
    Reinterpret float32 as int32 bits.
    endian: '=' native, '<' little-endian, '>' big-endian
    """
    return struct.unpack(f'{endian}i', struct.pack(f'{endian}f', value))[0]

def int32_to_float32(value, endian='<'):
    """
    Reinterpret int32 bits as float32.
    endian: '=' native, '<' little-endian, '>' big-endian
    """
    return struct.unpack(f'{endian}f', struct.pack(f'{endian}i', value))[0]

def parse_crs(wkt):
    crs = CRS(wkt)
    crs = crs.to_dict()
    return crs

def extract_albers_params(wkt):
    crs = parse_crs(wkt)
    info = {}
    info['datum'] = crs['datum']  
    info['proj_units'] = crs['units']
    info['first_parallel'] = crs['lat_1']
    info['sec_parallel'] = crs['lat_2']
    info['central_meridian'] = crs['lon_0']
    info['lat_origin'] = crs['lat_0']
    info['false_easting'] = crs['x_0']
    info['false_northing'] = crs['y_0']
    return info

def _keysearch(dictobj,keys,default):
    for key in keys:
        try:
            val = dictobj[key]
            if not val is None:
                return val
        except:
            pass
    return default

def _listlike(obj):
    if isinstance(obj,(list,tuple)):
        return True
    elif isinstance(obj,np.ndarray):
        if obj.ndim == 1:
            return True
    return False

def _qualify_datetime(dt):
    hectime = None
    strtime = None
    if isinstance(dt,str):
        strtime = dt
        try:
            hectime = HecTime(dt,60)
        except:
            logging.warning('Cannot convert {} to HecTime'.format(dt))    
    elif isinstance(dt, HecTime):
        hectime = dt
        strtime = dt.formatDate(format='%d%b%Y:%H%M')
    elif isinstance(dt,int):
        try:
            pytime = HecTime.getPyDateTimeFromValue(dt,60,0)
            hectime = HecTime.getHecTimeFromPyDateTime(pytime,60,0)
            strtime = hectime.formatDate(format='%d%b%Y:%H%M')
        except:
            logging.warning('Cannot convert integer value ({}) to HecTime'.format(dt))    
    else:
        logging.warning('Provided value ({}) cannot be converted to HecTime'.format(dt))
    return (hectime,strtime)    

class _GridInfo:
    # Parent class for GridInfo, GridHrapInfo, GridAlbersInfo and GridSpecifiedInfo
    # Provides methods to convert field values to int32 array and dictionary
    # Used inside the cython code towards the final grid write operation
    @classmethod
    def from_grid_type(cls,grid_type_info):
        if isinstance(grid_type_info,str): grid_type_info = grid_type_info.lower()
        if grid_type_info in ['hrap','hrap-time','hraptime','410','411',410,411]:
            return GridHrapInfo(grid_type=410)
        elif grid_type_info in ['alber','albers','albers-time','alberstime','alber-time','420','421',420,421]:
            return GridAlbersInfo(grid_type=420)
        elif grid_type_info in ['specified','spec','specified-time','specifiedtime','430','431',430,431]:
            return GridSpecifiedInfo(grid_type=430)
        else:
            return GridInfo(grid_type=400)

    def from_int_array(self,ar):
        pass

    def to_int_array(self):
        ginfo = self
        ibuff = []
        cls = type(ginfo)
        fields = cls()._fields_
        len = 0
        for name, typ in fields:
            if name.endswith('_length'):
                len = getattr(ginfo,name)

            if ctypes.sizeof(typ) <= 4: # or instanc of int and float
                # int, float, etc. data
                val = getattr(ginfo,name)
                if isinstance(val,(float,)):
                    val = float32_to_int32(val)
                ibuff.append(val)    

            elif ctypes.sizeof(typ) == 8:
                # pointer, array type 
                ptr = getattr(ginfo,name)
                for i in range(len):
                    val = ptr[i]
                    if isinstance(val,(float,)):
                        val = float32_to_int32(val)
                    ibuff.append(val)    
            else: 
                # > 8
                # fixed array type
                count = int(ctypes.sizeof(typ)/4)
                ptr = getattr(ginfo,name)
                for i in range(count):
                    val = ptr[i]
                    if isinstance(val,(float,)):
                        val = float32_to_int32(val)
                    ibuff.append(val)

        return np.array(ibuff,dtype=np.int32)

    def to_dict(self):
        ginfo = self
        info = {}
        cls = type(ginfo)
        fields = cls()._fields_
        len = 0
        for name, typ in fields:
            if name.endswith('_length'):
                len = getattr(ginfo,name)

            if ctypes.sizeof(typ) <= 4: # or instanc of int and float
                # int, float, etc. data
                val = getattr(ginfo,name)
                info[name] = val

            elif ctypes.sizeof(typ) == 8:
                # pointer, array type 
                ptr = getattr(ginfo,name)
                data = []
                for i in range(len):
                    val = ptr[i]
                    data.append(val)
                if not name.endswith(('_vals','_counts')):
                    # convert to string
                    data = ints_to_str(data)
                info[name] = data                  

            else: 
                # > 8
                # fixed array type
                count = int(ctypes.sizeof(typ)/4)
                data = []
                ptr = getattr(ginfo,name)
                for i in range(count):
                    val = ptr[i]
                    data.append(val)
                if not name.endswith(('_vals','_counts')):
                    # convert to string
                    data = ints_to_str(data)
                info[name] = data                  

        return info

    def get_fields(self):
        # get the name of parameters
        ginfo = self
        cls = type(ginfo)
        fields = cls()._fields_
        names = [name for name, typ in fields]
        return names

class GridInfo(_GridInfo,ctypes.Structure):
    _fields_ = [('info_fsize', ctypes.c_int32), # no need to specify in the profile dict while writing
                ('grid_type', ctypes.c_int32),  
                ('info_size', ctypes.c_int32),  # no need to specify while writing
                ('info_gsize', ctypes.c_int32), # no need to specify while writing
                ('stime', ctypes.c_int32),
                ('etime', ctypes.c_int32),
                ('data_units', ctypes.c_int32*3),
                ('data_type', ctypes.c_int32), 
                ('lower_left_x', ctypes.c_int32),
                ('lower_left_y', ctypes.c_int32),
                ('cols', ctypes.c_int32),
                ('rows', ctypes.c_int32),
                ('cell_size', ctypes.c_float), #
                ('compression_method', ctypes.c_int32), # defaults to zlib now
                ('opt_compression_elemsize', ctypes.c_int32), # no need to specify
                ('opt_compression_factor', ctypes.c_float),   # no need to specify
                ('opt_compression_base', ctypes.c_float),     # no need to specify
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32), # no need to specify while writing, max is 20
                ('range_table_vals', ctypes.c_float*20),
                ('range_table_counts', ctypes.c_int32*20),
                ]

class GridHrapInfo(_GridInfo,ctypes.Structure):
    _fields_ = [('info_fsize', ctypes.c_int32),
                ('grid_type', ctypes.c_int32),
                ('info_size', ctypes.c_int32),
                ('info_gsize', ctypes.c_int32),
                ('stime', ctypes.c_int32),
                ('etime', ctypes.c_int32),
                ('data_units', ctypes.c_int32*3),
                ('data_type', ctypes.c_int32),
                ('lower_left_x', ctypes.c_int32),
                ('lower_left_y', ctypes.c_int32),
                ('cols', ctypes.c_int32),
                ('rows', ctypes.c_int32),
                ('cell_size', ctypes.c_float), 
                ('compression_method', ctypes.c_int32),
                ('opt_compression_elemsize', ctypes.c_int32),
                ('opt_compression_factor', ctypes.c_float),
                ('opt_compression_base', ctypes.c_float),
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32),
                ('range_table_vals', ctypes.c_float*20),
                ('range_table_counts', ctypes.c_int32*20),
                ('data_source', ctypes.c_int32*3)             
                ]

class GridAlbersInfo(_GridInfo,ctypes.Structure):
    _fields_ = [('info_fsize', ctypes.c_int32),
                ('grid_type', ctypes.c_int32),
                ('info_size', ctypes.c_int32),
                ('info_gsize', ctypes.c_int32),
                ('stime', ctypes.c_int32),
                ('etime', ctypes.c_int32),
                ('data_units', ctypes.c_int32*3),
                ('data_type', ctypes.c_int32),
                ('lower_left_x', ctypes.c_int32),
                ('lower_left_y', ctypes.c_int32),
                ('cols', ctypes.c_int32), 
                ('rows', ctypes.c_int32),
                ('cell_size', ctypes.c_float),
                ('compression_method', ctypes.c_int32),
                ('opt_compression_elemsize', ctypes.c_int32),
                ('opt_compression_factor', ctypes.c_float),
                ('opt_compression_base', ctypes.c_float),
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32),
                ('range_table_vals', ctypes.c_float*20),
                ('range_table_counts', ctypes.c_int32*20),
                ('proj_datum', ctypes.c_int32),              
                ('proj_units', ctypes.c_int32*3),           
                ('first_parallel', ctypes.c_float),          
                ('sec_parallel', ctypes.c_float),            
                ('central_meridian', ctypes.c_float),        
                ('lat_origin', ctypes.c_float),              
                ('false_easting', ctypes.c_float),           
                ('false_northing', ctypes.c_float),          
                ('cell_zero_xcoord', ctypes.c_float),        
                ('cell_zero_ycoord', ctypes.c_float),        
                ]
    
class GridSpecifiedInfo(_GridInfo,ctypes.Structure):
    _fields_ = [('info_fsize', ctypes.c_int32),
                ('grid_type', ctypes.c_int32),                
                ('info_size', ctypes.c_int32),
                ('info_gsize', ctypes.c_int32),
                ('stime', ctypes.c_int32),                    
                ('etime', ctypes.c_int32),                    
                ('data_units', ctypes.c_int32*3),             
                ('data_type', ctypes.c_int32),                
                ('lower_left_x', ctypes.c_int32),             
                ('lower_left_y', ctypes.c_int32),            
                ('cols', ctypes.c_int32),                      
                ('rows', ctypes.c_int32),                     
                ('cell_size', ctypes.c_float),                
                ('compression_method', ctypes.c_int32),       
                ('opt_compression_elemsize', ctypes.c_int32),     
                ('opt_compression_factor', ctypes.c_float),       
                ('opt_compression_base', ctypes.c_float),         
                ('max_val', ctypes.c_float),                 
                ('min_val', ctypes.c_float),                 
                ('mean_val', ctypes.c_float),                
                ('range_length', ctypes.c_int32),
                ('range_table_vals', ctypes.c_float*20),      
                ('range_table_counts', ctypes.c_int32*20),    
                ('version', ctypes.c_int32),
                ('crs_name_length', ctypes.c_int32),           # no need to specify while writing
                ('crs_name', ctypes.POINTER(ctypes.c_int32)),
                ('crs_type', ctypes.c_int32),
                ('crs_def_length', ctypes.c_int32),            # no need to specify while writing
                ('crs_def', ctypes.POINTER(ctypes.c_int32)),   
                ('cell_zero_xcoord', ctypes.c_float),          
                ('cell_zero_ycoord', ctypes.c_float),          
                ('nodata', ctypes.c_float),                    
                ('tzid_length', ctypes.c_int32),               # no need to specify while writing 
                ('tzid', ctypes.POINTER(ctypes.c_int32)),      
                ('tzoffset', ctypes.c_int32),                  
                ('is_interval', ctypes.c_int32),               
                ('time_stamped', ctypes.c_int32),              
                ]

def _gridinfo_from_meta(info_dict):
    '''
    Inputs:
    ----------
    info_dict (dict): dictionary of parameters describing metadata of gridded data.
    
    Outputs:
    ----------
    gridinfo (GridInfo): Instance of GridInfo, GridHrapInfo, GridAlbersInfo or GridSpecifiedInfo. 

    '''
    # lowercase the string, remove opt_ from key and rebuild info_dict as info
    info = {} 
    for key,val in info_dict.items():
        key = key.lower()
        if key.startswith('opt_'):
            key = key[4:]
        if isinstance(val,str):
            pass
            #val = val.lower()
        info[key] = val

    logging.debug('gridinfo dict provided to _gridinfo_from_meta:\n{}'.format(info))    

    # grid_type
    # undefined
    info_obj = GridInfo()
    _grid_type = 400
    info_obj.grid_type = 400
    grid_type = info['grid_type']
    if isinstance(grid_type,str): grid_type = grid_type.lower()
    if grid_type in ['hrap','hrap-time','hraptime','410','411',410,411]:
        _grid_type = 410
        info_obj = GridHrapInfo()
        info_obj.grid_type = 410
    elif grid_type in ['alber','albers','albers-time','alberstime','alber-time','420','421',420,421]:
        _grid_type = 420
        info_obj = GridAlbersInfo()
        info_obj.grid_type = 420
    elif grid_type in ['specified','spec','specified-time','specifiedtime','430','431',430,431]:
        _grid_type = 430
        info_obj = GridSpecifiedInfo()
        info_obj.grid_type = 430

    # Process GridInfo
    #---------------------------------------------------------------------------------------------------------------------
    _info_flat_size = ctypes.sizeof(GridInfo) # 328 bytes = 82 int > than min required (63 ints) =  OK 
    _info_size = 124
    _info_gsize = 124
    
    # user supplied time or None
    _stime = _etime = 0 # expected to be in HecTime after data processing from below
    _stime0 = info.get('stime',None)
    _etime0 = info.get('etime',None)
    # hectime or None, string format time or None
    _stime1,_stime2 = _qualify_datetime(_stime0)   
    _etime1,_etime2 = _qualify_datetime(_etime0)   

    flag_time_issue = False
    if _stime0 is None or _stime1 is None:
        logging.debug('Start time in profile of grid is invalid or missing')
        flag_time_issue = True
        # info_obj.stime is already initialized to 0
    else:
        _stime = _stime1    
        info_obj.stime = _stime1.datetimeValue 

    if _etime0 is None or _etime1 is None:
        logging.debug('End time is not specified in profile of grid')
        flag_time_issue = True
        # info_obj.etime is already initialized to 0
    else:    
        _etime = _etime1    
        info_obj.etime = _etime1.datetimeValue 

    _temp = str_to_ints(info.get('data_units',''))[0:3]
    info_obj.data_units = (ctypes.c_int32*3)(*_temp)

    _data_type = info.get('data_type',None)
    _is_valid = False
    if _data_type is None:    
        logging.error("Missing grid data_type",exc_info=True)
        return # may be not necessary TODO:check
    if _data_type in GRID_DATA_TYPE.values():
        _is_valid = True
        info_obj.data_type = _data_type
    elif isinstance(_data_type,str):     
        _temp = _data_type.strip().lower()
        if _temp in GRID_DATA_TYPE.keys():
            _is_valid = 1
            info_obj.data_type = GRID_DATA_TYPE[_temp]

    if not _is_valid:    
        logging.error("Invalid grid data_type (={}).".format(_data_type),exc_info=True)
        return # may be not necessary TODO:check

    info_obj.lower_left_x = info.get('lower_left_x',0)
    info_obj.lower_left_y = info.get('lower_left_y',0)
    info_obj.cols = info['cols']
    info_obj.rows = info['rows']

    _cell_size = _keysearch(info,('cell_size','cellsize'),NODATA_FLOAT)
    info_obj.cell_size = _cell_size

    # out of order but need to do min,max and mean before compression
    _max_val = _keysearch(info,('max_val','max_value','max'),NODATA_FLOAT)
    _min_val = _keysearch(info,('min_val','min_value','min'),NODATA_FLOAT)
    _mean_val = _keysearch(info,('mean_val','mean_value','mean'),NODATA_FLOAT)

    # compression
    _comp = _keysearch(info,('compression_method','comp_method','compression','comp'),None)
    _comp_elemsize = _keysearch(info,('compression_elemsize','comp_elemsize'),NODATA_INT)
    _comp_factor = _keysearch(info,('compression_factor','comp_factor'),NODATA_FLOAT)
    _comp_base = _keysearch(info,('compression_base','comp_base'),NODATA_FLOAT)

    # allowing string for compression method too
    if _comp is None:
        _comp = UNDEFINED_COMPRESSION

    elif isinstance(_comp,str):
        _temp = _comp.lower()
        if _temp in ('undefined',):
            _comp = UNDEFINED_COMPRESSION
        elif _comp in ('none','nocomp','nocompression','no_comp','no-comp','no-compression'):
            _comp = NO_COMPRESSION
        elif _comp in ('zlib','deflate','zlib-deflate','zlib deflate','zlib_deflate'):
            _comp = ZLIB_DEFLATE_COMPRESSION

    else:        
        try:
            _comp = int(_comp)
        except:
            pass    

    if not _comp in (UNDEFINED_COMPRESSION,ZLIB_DEFLATE_COMPRESSION,NO_COMPRESSION): _comp = UNDEFINED_COMPRESSION

    if _comp == UNDEFINED_COMPRESSION:
        one_hour_in_milli = 1000*60*60
        if GRIDINFO_VERSION == 1 and not flag_time_issue:
            _interval = (_etime.python_datetime - _stime.python_datetime).total_seconds()*1000
            if one_hour_in_milli == _interval and _data_type == 1: #per-cum?
                _comp = PRECIP_2_BYTE
        else:
            _comp = ZLIB_DEFLATE_COMPRESSION        

    if _comp == PRECIP_2_BYTE:
        if _comp_base == NODATA_FLOAT and _comp_factor == NODATA_FLOAT:
            # adjust these values
            _comp_factor = 100.0
            _comp_base = 0.0
            if _min_val < _comp_base: _comp_base = math.floor(_min_val)
            no_comp_values = int((_max_val - _comp_base)*_comp_factor)
            if no_comp_values > 32768: # max no for 15 bits
                _comp_base = math.ceil(32767.0/(_max_val-_min_val))

    info_obj.compression_method = _comp
    info_obj.opt_compression_elemsize = _comp_elemsize
    info_obj.opt_compression_factor = _comp_factor
    info_obj.opt_compression_base = _comp_base
    # do actual compression outside this function

    info_obj.max_val = _max_val
    info_obj.min_val = _min_val
    info_obj.mean_val = _mean_val

    _rt_vals = _keysearch(info,('range_table_vals','range_table_values','range_values','range_vals'),[])
    _rt_counts = _keysearch(info,('range_table_counts','range_counts','range_counts'),[])
    if not (_listlike(_rt_vals) and _listlike(_rt_counts)):
        logging.error('range table values and counts needs to be either list or 1D array',exc_info=True)

    _rt_len = min(len(_rt_vals),len(_rt_counts),20)
    _rt_vals = _rt_vals[0:_rt_len]
    _rt_counts = _rt_counts[0:_rt_len]
    # range_table_counts is filled with zero when range_length or number of values is less than 20
    # following removes value and count corresponding to this
    end_zero_count = 0
    for i,x in enumerate(reversed(_rt_counts)):
        if x != 0:
            end_zero_count = i
            break

    _rt_vals = _rt_vals[0:len(_rt_vals)-end_zero_count]
    _rt_counts = _rt_counts[0:len(_rt_counts)-end_zero_count]
    _rt_len = len(_rt_vals)
    for i in range(_rt_len):
        info_obj.range_table_vals[i] = _rt_vals[i]
        info_obj.range_table_counts[i] = _rt_counts[i]
    info_obj.range_length = _rt_len    

    # Process HRAP 
    #---------------------------------------------------------------------------------------------------------------------
    if _grid_type == 410:
        _info_flat_size = ctypes.sizeof(GridHrapInfo) + 3*4 # could be atleast a pointer size (data_source pointer) larger than original = OK
        _info_size = 128
        _info_gsize = 124
        _data_source = _keysearch(info,('data_source','datasource','dsrc'),'')
        if not isinstance(_data_source,str):
            logging.warning('Data source for HRAP must be string')
            _data_source = ''
        _data_source = str_to_ints(_data_source)[0:3]
        _len = len(_data_source)
        if _len > 0:    
            info_obj.data_source = (ctypes.c_int32*_len)(*_data_source)

    # Process Albers
    #---------------------------------------------------------------------------------------------------------------------
    if _grid_type == 420:
        _info_flat_size = ctypes.sizeof(GridAlbersInfo) 
        _info_size = 164
        _info_gsize = 124
        _proj_datum = _keysearch(info,('proj_datum','project_datum','datum'),'')
        if isinstance(_proj_datum,int):
            if not (_proj_datum == NAD_27 or _proj_datum == NAD_83):
                _proj_datum = UNDEFINED_PROJECTION_DATUM
        else:
            if '83' in _proj_datum: 
                _proj_datum = NAD_83
            elif '27' in _proj_datum:
                _proj_datum = NAD_27
            else:
                _proj_datum = UNDEFINED_PROJECTION_DATUM        
        info_obj.proj_datum = _proj_datum

        _proj_units = _keysearch(info,('proj_units','projunits','proj_unit','projunit','project_units','projection_units','projection_unit'),'')
        if not isinstance(_proj_units,str):
            logging.warning('Project unit must be a string')
            _proj_units = ''
        _proj_units = str_to_ints(_proj_units)[0:3]    
        info_obj.proj_units = (ctypes.c_int32*3)(*_proj_units)

        _first_parallel = _keysearch(info,('first_parallel','firstparallel','first_par','par1','lat_1'),NODATA_FLOAT)
        _sec_parallel = _keysearch(info,('sec_parallel','secparallel','sec_par','sec1','second_parallel','lat_2'),NODATA_FLOAT)
        _central_meridian = _keysearch(info,('central_meridian','central_meridian','cmeridian','cmer','lon_0'),NODATA_FLOAT)
        _lat_origin = _keysearch(info,('lat_origin','latorigin','lat_0'),NODATA_FLOAT)
        _false_easting = _keysearch(info,('false_easting','false_east','easting','x_0'),NODATA_FLOAT)
        _false_northing = _keysearch(info,('false_northing','false_north','northing','y_0'),NODATA_FLOAT)
        _cell_zero_xcoord = _keysearch(info,('cell_zero_xcoord','cell0_xcoord','cell0_x'),NODATA_FLOAT)
        _cell_zero_ycoord = _keysearch(info,('cell_zero_ycoord','cell0_ycoord','cell0_y'),NODATA_FLOAT)

        info_obj.first_parallel = _first_parallel
        info_obj.sec_parallel = _sec_parallel
        info_obj.central_meridian = _central_meridian
        info_obj.lat_origin = _lat_origin
        info_obj.false_easting = _false_easting
        info_obj.false_northing = _false_northing
        info_obj.cell_zero_xcoord = _cell_zero_xcoord
        info_obj.cell_zero_ycoord = _cell_zero_ycoord

    # Process Specified
    #---------------------------------------------------------------------------------------------------------------------
    if _grid_type == 430:
        _info_flat_size = ctypes.sizeof(GridSpecifiedInfo) # later add size of variable length crs and time zone info
        _info_size = 160
        _info_gsize = 124
        #...
        _version = SPECIFIED_GRID_INFO_VERSION # hard-coded as java library

        _crs_name = _keysearch(info,('crs_name','srs_name'),'')
        _crs_name = str_to_ints(_crs_name)
        _crs_name_len = len(_crs_name)
        _crs_type = 0
        _crs_def = _keysearch(info,('crs_def','crs_definition','srs_def','srs_definition','crs','srs','grid_crs'),'')
        logging.debug("Parsed crs_def = <{}>".format(_crs_def))
        _crs_def = str_to_ints(_crs_def)
        logging.debug("Int crs_def = <{}>".format(_crs_def))
        _crs_def_len = len(_crs_def)
        _cell_zero_xcoord = _keysearch(info,('cell_zero_xcoord','cell0_xcoord','cell0_x'),NODATA_FLOAT)
        _cell_zero_ycoord = _keysearch(info,('cell_zero_ycoord','cell0_ycoord','cell0_y'),NODATA_FLOAT)

        _nodata = _keysearch(info,('nodata','no_data','novalue','no_value','null','null_value'),NODATA_FLOAT)
        _tzid = _keysearch(info,('tzid','tz_id','timezone','time_zone'),'')
        _tzid = str_to_ints(_tzid)
        _tzid_len = len(_tzid)
        _tz_offset = _keysearch(info,('tz_offset','tz_off','timezone_offset','time_zone_offset'),0.0) # NODATA_FLOAT??
        _is_interval = _keysearch(info,('is_interval','isinterval'),0) # NODATA_INT??
        _time_stamped = _keysearch(info,('time_stamped','is_time_stamped','timed'),0) # NODATA_INT??

        info_obj.version = _version
        info_obj.crs_name_length = _crs_name_len
        if _crs_name_len > 0:
            info_obj.crs_name = (ctypes.c_int32*_crs_name_len)(*_crs_name)
        info_obj.crs_type = _crs_type
        info_obj.crs_def_length = _crs_def_len
        if _crs_def_len > 0:
            info_obj.crs_def= (ctypes.c_int32*_crs_def_len)(*_crs_def)
        info_obj.cell_zero_xcoord = _cell_zero_xcoord
        info_obj.cell_zero_ycoord = _cell_zero_ycoord

        info_obj.nodata = _nodata
        info_obj.tzid_length = _tzid_len
        if _tzid_len > 0:
            info_obj.tzid = (ctypes.c_int32*_tzid_len)(*_tzid)
        info_obj.tz_offset = _tz_offset
        info_obj.is_interval = _is_interval
        info_obj.time_stamped = _time_stamped
        _info_flat_size = _info_flat_size + _crs_name_len*4 + _crs_def_len*4 + _tzid_len*4

    info_obj.info_fsize = _info_flat_size
    info_obj.info_size = _info_size
    info_obj.info_gsize = _info_gsize

    return info_obj

def _convert_grid7_to_grid6_meta(gstruct,pathname=None):
    # get gridinfo from grid struct
    if not pathname:
        pathname = gstruct.pathname()

    info_dict = gstruct.profile
    stats = gstruct.stats()
    info_dict['max_value'] = stats['max']
    info_dict['min_value'] = stats['min']
    info_dict['mean_value'] = stats['mean']
    info_dict['range_table_vals'] = stats['range_values'][0:20]
    info_dict['range_table_counts'] = stats['range_counts'][0:20] # TODO: warn if > 20
    info_dict['range_length'] = len(info_dict['range_table_vals'])
    info_dict['compression_elemsize'] = NODATA_INT                # TODO:DSS7 actually stores this value
    info_dict['compression_factor'] = 0.0 # these two are not implemented in DSS7 as of 8/13/2025 and set to zero in source C code line 204 - 206.
    info_dict['compression_base'] = 0.0
    pathobj = DssPathName(pathname)
    info_dict['stime'] = pathobj.getDPart()
    info_dict['etime'] = pathobj.getEPart()
    info_dict.pop('grid_transform')

    # grid type: Albers, Hrap, Specified or undefined
    _gtype = info_dict['grid_type'] # string type
    _gtype = GRID_TYPE[_gtype]
    
    # GridInfo object
    cols = gstruct.width
    rows = gstruct.height
    cell_size = gstruct.cellsize()
    nodata = gstruct.nodata
    info_dict.update({'rows':rows,'cols':cols,'cell_size':cell_size,'nodata':nodata})

    if _gtype < 420 and _gtype > 409:
        pass
    elif _gtype < 430:
        #Albers
        grid_crs = info_dict.get('grid_crs','').strip()
        if grid_crs:
            try:
                params = extract_albers_params(grid_crs)
                info_dict.update(params)
            except:
                pass    

    elif _gtype < 440:
        # Specified
        grid_crs = info_dict.pop('grid_crs','')
        crs_name = info_dict.pop('opt_crs_name','')
        info_dict['crs_name'] = crs_name
        info_dict['crs_def'] = grid_crs

    logging.debug('GRID7 info extracted in GRID6 format: \n{}'.format(info_dict))
    return info_dict