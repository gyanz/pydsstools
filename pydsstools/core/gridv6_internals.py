'''
This module provides data structures and methods for interacting with DSS 6 grids. 
Since the implementation in this file is subject to change, direct use of this module is not recommended.
* Use pydsstools.heclib.dss.Heclib.Open.put_grid6 to write grid to dss 6 file.
* Currently grid data is read from dss file using read_grid method. DSS 6 grid is read and converted to DSS 7 form using C++ code.
'''
import logging
import struct
import ctypes
import math
import numpy as np
from . import HecTime,DssPathName
from .gridinfo import GridInfoCreate

__all__ = ['GridInfo6','HrapInfo6','AlbersInfo6','SpecifiedInfo6',
           'gridinfo7_to_gridinfo6',

          ]
# It looks like GridInfo Version in DSSVue is either 2 (Specified grid) or 1 (other grids)
# Only Specified GridInfo has _version parameter which is set to 2 in pydsstools
# GridInfo shows up as 1 for other grids even though this parameter is not set in pydsstools
SPECIFIED_GRID_INFO_VERSION = 2
GRIDINFO_VERSION = 1

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

class _GridInfo6:
    # Parent class for GridInfo, GridHrapInfo, GridAlbersInfo and GridSpecifiedInfo
    # Provides methods to convert field values to int32 array and dictionary
    # Used inside the cython code towards the final grid write operation
    def version(self):
        return GRIDINFO_VERSION

    @classmethod
    def from_grid_type(cls,grid_type_info):
        if isinstance(grid_type_info,str): grid_type_info = grid_type_info.lower()
        if grid_type_info in ['hrap','hrap-time','hraptime','410','411',410,411]:
            return HrapInfo6(grid_type=410)
        elif grid_type_info in ['alber','albers','albers-time','alberstime','alber-time','420','421',420,421]:
            return AlbersInfo6(grid_type=420)
        elif grid_type_info in ['specified','spec','specified-time','specifiedtime','430','431',430,431]:
            return SpecifiedInfo6(grid_type=430)
        else:
            return GridInfo6(grid_type=400)

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

            if ctypes.sizeof(typ) <= 4:
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

            if ctypes.sizeof(typ) <= 4:
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
    
    def to_gridinfo7(self):
        prof7 = gridinfo6_to_gridinfo7_compatible_dict(self)
        return GridInfoCreate(**prof7)


class GridInfo6(_GridInfo6,ctypes.Structure):
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
                ('compression_size', ctypes.c_int32), # no need to specify
                ('compression_factor', ctypes.c_float),   # no need to specify
                ('compression_base', ctypes.c_float),     # no need to specify
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32), # no need to specify while writing, max is 20
                ('range_vals', ctypes.c_float*20),
                ('range_counts', ctypes.c_int32*20),
                ]

class HrapInfo6(_GridInfo6,ctypes.Structure):
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
                ('compression_size', ctypes.c_int32),
                ('compression_factor', ctypes.c_float),
                ('compression_base', ctypes.c_float),
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32),
                ('range_vals', ctypes.c_float*20),
                ('range_counts', ctypes.c_int32*20),
                ('data_source', ctypes.c_int32*3)             
                ]

class AlbersInfo6(_GridInfo6,ctypes.Structure):
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
                ('compression_size', ctypes.c_int32),
                ('compression_factor', ctypes.c_float),
                ('compression_base', ctypes.c_float),
                ('max_val', ctypes.c_float),
                ('min_val', ctypes.c_float),
                ('mean_val', ctypes.c_float),
                ('range_length', ctypes.c_int32),
                ('range_vals', ctypes.c_float*20),
                ('range_counts', ctypes.c_int32*20),
                ('proj_datum', ctypes.c_int32),              
                ('proj_units', ctypes.c_int32*3),           
                ('first_parallel', ctypes.c_float),          
                ('sec_parallel', ctypes.c_float),            
                ('central_meridian', ctypes.c_float),        
                ('lat_origin', ctypes.c_float),              
                ('false_easting', ctypes.c_float),           
                ('false_northing', ctypes.c_float),          
                ('xcoord_cell0', ctypes.c_float),        
                ('ycoord_cell0', ctypes.c_float),        
                ]
    
class SpecifiedInfo6(_GridInfo6,ctypes.Structure):
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
                ('compression_size', ctypes.c_int32),     
                ('compression_factor', ctypes.c_float),       
                ('compression_base', ctypes.c_float),         
                ('max_val', ctypes.c_float),                 
                ('min_val', ctypes.c_float),                 
                ('mean_val', ctypes.c_float),                
                ('range_length', ctypes.c_int32),
                ('range_vals', ctypes.c_float*20),      
                ('range_counts', ctypes.c_int32*20),    
                ('version', ctypes.c_int32),
                ('crs_name_length', ctypes.c_int32),           # no need to specify while writing
                ('crs_name', ctypes.POINTER(ctypes.c_int32)),
                ('crs_type', ctypes.c_int32),
                ('crs_def_length', ctypes.c_int32),            # no need to specify while writing
                ('crs_def', ctypes.POINTER(ctypes.c_int32)),   
                ('xcoord_cell0', ctypes.c_float),          
                ('ycoord_cell0', ctypes.c_float),          
                ('nodata', ctypes.c_float),                    
                ('tzid_length', ctypes.c_int32),               # no need to specify while writing 
                ('tzid', ctypes.POINTER(ctypes.c_int32)),      
                ('tzoffset', ctypes.c_int32),                  
                ('is_interval', ctypes.c_int32),               
                ('time_stamped', ctypes.c_int32),              
                ]


def gridinfo6_init_from_grid_type(grid_type):
    if grid_type == 400:
        return GridInfo6()
    elif grid_type == 410:
        return HrapInfo6()
    elif grid_type == 420:
        return AlbersInfo6()
    elif grid_type == 430:
        return SpecifiedInfo6()

def gridinfo7_to_gridinfo6(gridinfo7,pathname):
    grid_type = gridinfo7.get_v6_grid_type() # enum
    grid_type = grid_type.value
    info6 = _GridInfo6.from_grid_type(grid_type)
    info7 = gridinfo7

    # Common paramters found in all (i.e., Gridinfo in V6)
    # -----------------------------------------
    # start and end time from dss pathname
    path = DssPathName(pathname)
    dpart = path.getDPart()
    epart = path.getEPart()
    flag_time = False
    try:
        stime = HecTime(dpart,60)
        info6.stime = stime.datetimeValue
    except:
        stime = 0
        flag_time = True    

    try:
        etime = HecTime(epart,60)
        info6.etime = etime.datetimeValue
    except:
        etime = 0
        flag_time = True

    # data_units
    data_units = str_to_ints(info7.data_units)
    if len(data_units) > 3:
        logging.warning('data_units was truncated during conversion to grid v6')    
    info6.data_units = (ctypes.c_int32*3)(*data_units[0:3])

    # data_type
    info6.data_type =  info7.data_type.value
    info6.lower_left_x = info7.lower_left_cell[0]  
    info6.lower_left_y = info7.lower_left_cell[1]
    info6.rows = info7.shape[0]  
    info6.cols = info7.shape[1]
    info6.cell_size = info7.cell_size

    # compression
    comp_method = info7.compression_method.value
    comp_base = info7.compression_base
    comp_factor = info7.compression_factor


    info6.compression_method = comp_method
    info6.compression_base = comp_base
    info6.compression_factor = comp_factor

    # stats
    info6.max_val = info7.max_val
    info6.min_val = info7.min_val
    info6.mean_val = info7.mean_val
    range_vals = info7.range_vals
    range_counts = info7.range_counts
    end = 0
    for i,count in enumerate(reversed(range_counts)):
        if count != 0:
            end = i
            break
    range_length = len(range_counts) - end
    range_length = min(len(range_vals),range_length,20)
    info6.range_length = range_length
    for i in range(range_length):
        info6.range_vals[i] = info7.range_vals[i]    
        info6.range_counts[i] = info7.range_counts[i]    

    # GridInfo in v6, UndefineGridInfo in v7
    # -----------------------------------------
    if grid_type == 400:
        info_flat_size = ctypes.sizeof(GridInfo6)
        info_size = 124
        info_gsize = 124

    # HRAP
    # -----------------------------------------
    elif grid_type == 410:
        # flat size could be a pointer size (i.e.,data_source pointer) 
        # larger than that is necessary, which is OK
        info_flat_size = ctypes.sizeof(HrapInfo6) + 3*4 
        info_size = 128
        info_gsize = 124

        # data_source
        data_source = str_to_ints(info7.data_source)
        if len(data_source) > 3:
            logging.warning('data_source was truncated during conversion to grid v6')    
        info6.data_source = (ctypes.c_int32*3)(*data_source[0:3])

    # Albers
    # -----------------------------------------
    elif grid_type == 420:
        info_flat_size = ctypes.sizeof(AlbersInfo6) 
        info_size = 164
        info_gsize = 124

        # projection
        # need to handle garbage value enum.invalid later
        info6.proj_datum = info7.proj_datum.value
        proj_units = str_to_ints(info7.proj_units)
        if len(proj_units) > 3:
            logging.warning('proj_unit was truncated during conversion to grid v6')    
        info6.proj_units = (ctypes.c_int32*3)(*proj_units[0:3])
        info6.lat_origin = info7.lat_0
        info6.first_parallel = info7.lat_1
        info6.sec_parallel = info7.lat_2
        info6.central_meridian = info7.lon_0
        info6.false_easting = info7.x_0
        info6.false_northing = info7.y_0
        info6.xcoord_cell0 = info7.coords_cell0[0]
        info6.ycoord_cell0 = info7.coords_cell0[1]


    # Specified    
    # -----------------------------------------
    elif grid_type == 430:
        info_flat_size = ctypes.sizeof(SpecifiedInfo6) 
        info_size = 160
        info_gsize = 124

        info6.version = SPECIFIED_GRID_INFO_VERSION
        # crs
        crs_name = str_to_ints(info7.crs_name)
        count = len(crs_name)
        if count > 0: info6.crs_name = (ctypes.c_int32*count)(*crs_name)
        info6.crs_name_length = count
        info_flat_size += count
        # crs definition
        crs = str_to_ints(info7.crs)
        count = len(crs)
        info6.crs_def_length = count
        if count > 0: info6.crs_def = (ctypes.c_int32*count)(*crs)
        info_flat_size += count
        # cell zero
        info6.xcoord_cell0 = info7.coords_cell0[0]
        info6.ycoord_cell0 = info7.coords_cell0[1]
        # time zone
        tzid = str_to_ints(info7.tzid)
        count = len(tzid)
        info6.tzid_length = count
        if count > 0: info6.tzid = (ctypes.c_int32*count)(*tzid)
        info_flat_size += count
        info6.tz_offset = info7.tzoffset 
        info6.is_interval = int(info7.is_interval) 
        info6.time_stamped = int(info7.time_stamped)

    info6.info_fsize = info_flat_size    
    info6.info_size = info_size    
    info6.info_gsize = info_gsize
    return info6    

def gridinfo6_to_gridinfo7_compatible_dict(gridinfo6):
    prof6 = gridinfo6.to_dict()
    grid_type = prof6['grid_type']

    llx = prof6.pop('lower_left_x')
    lly = prof6.pop('lower_left_y')
    prof6['lower_left_cell'] = (llx,lly)

    rows = prof6.pop('rows')
    cols = prof6.pop('cols')
    prof6['shape'] = (rows,cols)

    prof6.pop('range_length')

    if grid_type == 420:
        xcoord = prof6.pop('xcoord_cell0')
        ycoord = prof6.pop('ycoord_cell0')
        prof6['coords_cell0'] = (xcoord,ycoord)

    if grid_type == 430:
        xcoord = prof6.pop('xcoord_cell0')
        ycoord = prof6.pop('ycoord_cell0')
        prof6['coords_cell0'] = (xcoord,ycoord)

        prof6.pop('version')
        prof6.pop('crs_name_length')
        prof6.pop('crs_def_length')
        prof6.pop('tzid_length')

    return prof6