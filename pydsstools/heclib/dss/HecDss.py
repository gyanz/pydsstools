"""
 Open class object for HEC-DSS file
"""
__all__ = ['Open']

import logging
from copy import copy
from array import array
from datetime import datetime
import numpy as np
import numpy.ma as ma
import pandas as pd
from datetime import datetime
from os import PathLike
from pathlib import Path
import numpy.typing as npt # npt.NDArray[np.float32], npt.Arraylike
from pydantic import validate_call
from typing import (
    Any, Optional, Union, Tuple, List, Dict, Set,
    Iterable, Iterator, Sequence, Mapping, MutableMapping,
    Callable, overload, TypedDict, Final, ClassVar,
    TypeVar, Generic, NoReturn
)

try:
    # python 3.10+
    from typing import Annotated,TypeAlias,Literal
except:
    # 3.8 <= python < 3.10
    from typing_extensions import Annotated,TypeAlias,Literal

from ...core import Open as _Open
from ...core import TimeSeriesStruct,TimeSeriesContainer
from ...core import PairedDataStruct,PairedDataContainer
from ...core import SpatialGridStruct
from ...core.gridinfo import GridInfo,GridType
from ...core.gridv6_internals import gridinfo7_to_gridinfo6,GridInfo6
from ...core import getPathnameCatalog, deletePathname,PairedDataContainer,HecTime,DssPathName,dss_info
from ...heclib.utils import compute_grid_stats,UNDEFINED
from ...heclib import gridv6

DateLike = TypeVar('DateLike',str,datetime,HecTime)
DateWindow: TypeAlias = Tuple[DateLike,DateLike]
PathType: TypeAlias = Union[str,Path,PathLike]

class Open(_Open):
    """Open a DSS file and create a dataset object that supports input/output operations.

    This class provides an interface for reading from and writing to DSS files,
    enabling manipulation of time series, paired-data and gridded records 
    contained within the file. 
    
    """
    #@validate_call
    def __init__(self,dss_path:PathType,version:Optional[Literal[6,7]]=None,mode:Literal['rw','r']='rw') ->None:
        """
        Parameter
        ---------
        dss_path:
            Path of the dss file.
        version:
            Version of the DSS file. Supported versions are 6 (legacy) and 7 (latest).  
            When opening an existing file, the specified version must match the file's version.  
            Setting this parameter to None will automatically detect and use the correct version.  
            When opening a new file (if the specified file does not exist), using None will create a version 7 file.
        mode:
            Optional string specifying the mode in which the DSS file is opened.  
            Defaults to 'rw', which allows both reading from and writing to the file.  
            Use 'r' to open the file in read-only mode.

        Returns
        --------
        None        
        """
        super().__init__(dss_path,version)
        self.mode = mode

    #@validate_call
    def read_ts(self,pathname:Union[str,Path,PathLike],window:Optional[DateWindow]=None,trim_missing:bool=False,regular:bool=True,window_flag:Literal[0,1,1,3]=0) ->TimeSeriesStruct:
        """Read time-series record

        Parameter
        ---------
        pathname: 
            dss record pathname

        window: 
            tuple of start and end dates. If it is None, uses date from D-part of pathname.

        regular: bool, default True
            If False, the read data is treated as irregular time-series.

        trim_missing: bool,default True, applies to regular time-series only
            Removes missing values at the beginning and end of data set

        window_flag: integer 0,1,2 or 3, default 0, applies to irregular time-series only
                        0 - adhere to time window
                        1 - Retrieve one value previous to start of time window
                        2 - Retrieve one value after end of time window
                        3 - Retrieve one value before and one value after time window

        Returns
        --------
            TimeSeriesStruct

        Examples
        ---------
            >>> ts = fid.read_ts(pathname,window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))
            >>> ts = fid.read_ts(pathname,regular=False)

        """
        retrieve_flag = 0 # adhere to window

        if regular:
            retrieve_flag = -1 if trim_missing else retrieve_flag

        else:
            if window_flag in [0,1,2,3]:
                retrieve_flag = window_flag
            else:
                logging.error('Invalid window_flag for irregular dss record')
                return

        if not window:
            pathobj=DssPathName(pathname)
            retrieve_all = 0
            if not pathobj.getDPart().strip(): # if date part is empty, retrieve all data ignoring date
                retrieve_all = 1
            return super().read_path(pathname,retrieve_flag,boolRetrieveAllTimes=retrieve_all)

        startdate, enddate = window
        if isinstance(startdate, str):
            startdate = HecTime.getPyDateTimeFromString(startdate)
        elif not isinstance(startdate,datetime):
            logging.error('startdate is not string or datetime object')
            return

        if isinstance(enddate, str):
            enddate = HecTime.getPyDateTimeFromString(enddate)
        elif not isinstance(enddate,datetime):
            logging.error('enddate is not string or datetime object')
            return

        sday = startdate.strftime('%d%b%Y')
        stime = startdate.strftime('%H:%M:%S')
        eday = enddate.strftime('%d%b%Y')
        etime = enddate.strftime('%H:%M:%S')

        return super().read_window(pathname,sday,stime,eday,etime,retrieve_flag)


    #@validate_call
    def put_ts(self,tsc:TimeSeriesContainer,prevent_overflow:Optional[bool]=True) ->None:
        """Write time-series

        Parameter
        ---------
            tsc: TimeSeriesContainer

            prevent_overflow: bool, default True, applies to irregular time-series only  
                  times are int32 values with origin (or Julian Base date) at 01Jan1900 00:00:00, 
                  and can overflow for large/extreme dates or small granularity. To prevent int32 overflow, 
                  the supplied minimum date is used as the origin. This may still overflow if
                  extreme dates are supplied. In such case, write time-series data one at a time or 
                  in a group with less extreme date variation.

        Returns
        --------
            None

        Usage
        ---------
            >>> ts = fid.read_ts(pathname,window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))
            >>> ts = fid.read_ts(pathname,regular=False)
        """
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return
        
        
        if tsc.interval > 0:
            # Regular time-series
            if not len(tsc.values) == tsc.numberValues:
                logging.error('numberValues attribute of TimeSeriesContainer not equal to length of values')
                return
            # check start datetime format
            sdate = tsc.startDateTime
            try:
                sdate = HecTime(sdate,tsc.granularity)
            except:
                logging.warning('Start datetime of regular time-series ({}) may be incorrect'.format(tsc.startDateTime))
            else:
                sdate = sdate._toString(end_of_day=False)    
                tsc.startDateTime = sdate
            super().put(tsc)

        else:
            # Irregular time-series
            times = tsc.times
            times_copy = copy(times)
            values_copy = copy(tsc.values)
            julianbasedate = 0
            time_values = []

            if times is None or not len(times):
                logging.error('times for irregular time-series is not non-empty list, tuple, or array')
                return

            if not (tsc.numberValues == len(times)):
                logging.error('times does not have correct number of elements')
                return

            if not isinstance(times[0],(str,datetime)):
                logging.error('times element must be datetime string or python datetime object')
                return
            
            '''
            if tsc.granularity == 1:
                # TODO: Implement more restrictions with second granularity
                pathobj=DssPathName(tsc.pathname)
                epart = pathobj.getEPart().strip().upper()
                if epart in ['IR-MONTH','IR-YEAR','IR-DECADE','IR-CENTURY']:
                    logging.error('Granularity must be minute or larger')
                    return
            '''

            if isinstance(times[0],str) and prevent_overflow:
                times = [HecTime.getPyDateTimeFromString(x) for x in times]

            if isinstance(times[0],datetime):
                min_date = min(times)
                _julianbasedate = min_date.strftime('%d%b%Y')
                julianbasedate = HecTime.getJulianDaysFromDate(_julianbasedate)
                tsc._startDateBase = _julianbasedate

            for i in range(tsc.numberValues):
                tm = HecTime(times[i],tsc.granularity,julianbasedate)
                time_values.append(tm.datetimeValue)

            values = tsc.values
            try:
                values = values.tolist()
            except:
                pass
            key_val = sorted(zip(time_values,values),key=lambda x:x[0])

            try:
                tsc.times = [t for t,v in key_val]
                tsc.values = [v for t,v in key_val]
                super().put(tsc)
            finally:
                tsc.times = times_copy
                tsc.values = values_copy


    #@validate_call
    def read_pd(self,pathname:PathType,window:Optional[DateWindow]=None,dtype:Optional[np.dtype]=None,dataframe:Optional[bool]=True) ->pd.DataFrame:
        """Read paired data as pandas dataframe

        Parameter
        ---------
            pathname: string, dss record pathname

            window: tuple, default None
                    tuple of (starting row, ending row, starting curve, ending curve) indices.
                    If None, read all data.
                    starting row, starting curve >= 1, i.e., first row or curve is 1, not 0.
                    ending row, ending curve <= total rows/ordinates in paired data or <=0 ...
                    0 can be used to specify last row or curve. Negative number works like indexing of python list.

            dtype: numpy dtype, default None
                  Data type of returned DataFrame

            dataframe: boolean, default True
                  Returns dataframe object if True, otherwise ruturns paired data structure

        Returns
        --------
            DataFrame object


        Usage
        ---------
            >>> fid.read_pd(pathname,window=(2,5))
            >>> fid.read_pd(pathname)
        """
        if window:
            size_info = self.pd_info(pathname)
            total_ordinates = size_info['data_no']
            total_curves = size_info['curve_no']
            start_ord,end_ord,start_curve,end_curve = window
            if end_ord <= 0:
                end_ord = total_ordinates + end_ord
            if end_curve <= 0:
                end_curve = total_curves + end_curve
            if not (start_ord >=1 and end_ord <= total_ordinates and end_ord >= start_ord):
                logging.error('Ordinate indices of window out of bounds')
                return
            if not (start_curve >=1 and end_curve <= total_curves and end_curve >= start_curve):
                logging.error('Curve indices of window out of bounds')
                return
            window = (start_ord,end_ord,start_curve,end_curve)

        pds = super().read_pd(pathname,window)
        if dataframe:
            x,curves,label_list = pds.get_data()
            tb = np.asarray(curves).T
            # The row in curves array contains curve data
            # Transpose causes the curve data to be in columns (for DataFrame purpose)
            if label_list:
                label_list = [x.strip() for x in label_list]
            else:
                for i in range(tb.shape[1]):
                    label_list.append(' ')
            if not len(label_list) == tb.shape[1]:
                logging.warn('Number of labels is not equal to number of curves. This issue can occur with preallocated paired data.')
                label_list = [str(i+1) for i in range(curves.shape[1])]

            indx=list(x[0])
            df = pd.DataFrame(data=tb,index=indx,columns=label_list,dtype=dtype,copy=True)
            df.index.name="X"
            return df
        else:
            return pds

    #@validate_call
    def read_pd_labels(self,pathname:PathType):
        _df = self.read_pd(pathname,window=(1,1,1,0))
        df = pd.DataFrame(data=_df.columns,columns=['label'])
        return df

    #@validate_call
    def put_pd(self,pdc_df_array:Union[PairedDataContainer,pd.DataFrame,np.ndarray],curve_index:Optional[int]=None,**kwargs:Any) ->None:
        """Write paired new or edit existing data series

        Parameter
        ---------
            pdc_df_array: PairedDataContainer, pandas dataframe or numpy array

            curve_index: curve or column number, default None
                         Data in specified curve is changed.

            window: tuple consisting of starting and ending row numbers or ordinates
                    Used only when curve_index is specified

            kwargs: arguments or attributes of PairedDataContainer
                    e.g., pathname, labels_list, etc. While writing single column or curve
                    of preallocated pds, labels_list can be specified to
                    update the label that was set during preallocation.

        Returns
        --------
            None


        Usage
        ---------
            >>> fid.put_pd([1,2,3,4],2,window=(2,5),pathname='...',labels_list=['Curve 2'])

        """
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        pdc = pdc_df_array
        if isinstance(pdc_df_array,pd.DataFrame):
            pdc = PairedDataContainer(**kwargs)
            pdc.independent_axis = pdc_df_array.index.values
            pdc.curves = pdc_df_array.values.T
            pdc.curve_no = pdc.curves.shape[0]
            pdc.data_no = pdc.curves.shape[1]
            pdc.labels_list = pdc_df_array.columns.tolist()

        elif not curve_index is None:
            pathname = kwargs['pathname']
            labels_list = kwargs.get('labels_list',[])
            window = kwargs.get('window',None)

            size_info = self.pd_info(pathname)
            total_ordinates = size_info['data_no']
            total_curves = size_info['curve_no']
            max_label_size = size_info['label_size']

            if not (curve_index >=1 and curve_index <= total_curves):
                logging.error('Curve index out of bounds.')
                return

            start_ord,end_ord = (1,total_ordinates)
            if window:
                start_ord,end_ord = window
                if end_ord <= 0:
                    end_ord = total_ordinates + end_ord
                if not (start_ord >=1 and end_ord <= total_ordinates and end_ord >= start_ord):
                    logging.error('Ordinate indices of window out of bounds')
                    return

            if isinstance(pdc_df_array,(array,list,tuple)):
                pdc_df_array = np.array(pdc_df_array,np.float32)
            elif isinstance(pdc_df_array,np.ndarray):
                pass
            else:
                raise BaseException('Unsupported data provided')

            pdc_df_array = np.reshape(pdc_df_array,[1,-1])
            arr_size = pdc_df_array.size
            if not arr_size == (end_ord - start_ord + 1):
                logging.error('Incorrect size of array provided')
                return
            pdc = PairedDataContainer(pathname=pathname,labels_list=labels_list)
            pdc.curves = pdc_df_array
            super().put_one_pd(pdc,curve_index,(start_ord,end_ord), max_label_size)
            return

        super().put_pd(pdc)

    #@validate_call
    def preallocate_pd(self,pdc_or_shape:Union[Tuple[int,int],pd.DataFrame,np.ndarray],**kwargs:Any) ->None:
        # Each curve is allocated 10 characters by default if label_size is not specified
        # Curves are labeled 1,2,3 ... by default
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        pdc = pdc_or_shape
        if isinstance(pdc_or_shape,(list,tuple)):
            pdc = PairedDataContainer(**kwargs)
            pdc.data_no = pdc_or_shape[0]
            pdc.curve_no = pdc_or_shape[1]
            pdc.independent_axis = array('f',[i+1 for i in range(pdc.data_no)])
            if not pdc.labels_list:
                pdc.labels_list = [str(i+1) for i in range(pdc.curve_no)]
        label_size = max(10,kwargs.get('label_size',10))
        super().prealloc_pd(pdc,label_size)

    #@validate_call
    def read_grid(self,pathname:PathType,metadata_only:Optional[bool]=False) ->SpatialGridStruct:
        """Read spatial grid. Version 0 (DSS-6 format) grid is returned in DSS-7 format.
        """
        sg_st = SpatialGridStruct()
        retrieve_data = 0 if metadata_only else 1
        super().read_grid(pathname,sg_st,retrieve_data)
        return sg_st

    def read_grid2(self,pathname:PathType,metadata_only:Optional[bool]=False) ->Any:
        """Reads both version 0 (DSS-6 format) and 100 (DSS-7 format) spatial grid data.

        DSS-7 grid is returned as SpatialgridStruct whilw DSS-6 grid is returned as tuple of np.array and gridinfo.
        """
        retrieve_data = False if metadata_only else True
        grid_ver = self._get_gridver(pathname)
        if grid_ver is None:
            logging.error('Invalid grid data or version')
        elif grid_ver != 0:
            logging.info('Reading modern format (DSS7) grid')
            return self.read_grid(pathname,retrieve_data)
        else:
            logging.info('Reading older format (DSS6 or grid version 0) grid')
            # find grid_type and create info6
            grid_type = self._get_gridtype(pathname)
            info6 = GridInfo6.from_grid_type(grid_type)
            if grid_type == 430:
                # add space for crs defination, tz id generously
                # it should be more than what is in the file
                info6 = GridInfo6.get_specinfo6(50,200,50)
            #info6 is updated with data from the dss file
            data = super()._read_grid0(pathname,info6,retrieve_data)
            if metadata_only:
                if not data is None:
                    return info6.to_gridinfo7()
            if not data is None:
                info = info6.to_gridinfo7()
                return data,info        
        
    #@validate_call
    def put_grid(self, data:Union[SpatialGridStruct,np.array], pathname:Optional[PathType]=None, gridinfo:Optional[GridInfo]=None, flipud:Optional[bool]=True, compute_stats:Optional[Union[bool,List[float]]]=True, transform:Optional[Any]=None) ->None:
        """Write spatial grid to DSS-7 file. Writing to DSS-6 file not allowed.

        Parameter
        ---------
        data : SpatialGridStruct or numpy.ndarray or numpy.ma.MaskedArray
            Grid data to write.
            - **numpy.ndarray**: `np.nan` and `nodata` values (from `gridinfo`) are treated as nodata.
            - **numpy.ma.MaskedArray**: masked elements are treated as nodata.
            - **SpatialGridStruct**: a structured object containing grid and metadata.

        pathname : PathType, optional
            Pathname for the DSS record. It can be None for SpatialGridStruct. The dates in parts D and E are automaticallu
            reformatted to correct convention. Part D uses the beggining of the day (e.g., ``02JAN2025:0000``) while Part E
            uses the end of the previous day convention (e.g., ``01JAN2025:2400``).   

        gridinfo : GridInfo or subclass, optional
            Metadata describing the grid. Can be one of:
            - `GridInfo`, `HrapInfo`, or `AlbersInfo`: requires `data_type`, `cell_size`.
            - `SpecifiedInfo`: requires `data_type`, `cell_size`, and `nodata`.

        flipud : bool, default=True
            If True, flips the rows of the data array upside down before writing.

        compute_stats : bool or list of float, default=True
            Controls whether and how statistics are computed for the grid data:
            - **True**: compute min, max, mean, range, and range counts.
            - **False**: do not compute statistics.
            - **list of float**: compute "greater than or equal to" counts for the specified values
            (maximum of 19 thresholds, excluding nodata).

        transform : Any, optional
            Spatial transform information (e.g., affine transform). If provided, it
            overrides transform parameters in `gridinfo`.
             
        """
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        if self.version == 6:
            logging.warning('Writing DSS grid record in DSS-6 file is not supported')
            return

        if isinstance(data, SpatialGridStruct):
            # use this for copying from one file to another or updating statistics
            if pathname is None: pathname = data.pathname
            gridinfo = data.gridinfo
            grid_type = gridinfo.grid_type
            shape = gridinfo.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata

            if compute_stats:
                # nodata is taken care within read method to give masked data
                _mdata = data.read()
                stats = compute_grid_stats(_mdata,compute_stats)
                stats['range_vals'][0] = UNDEFINED
                gridinfo.max_val = stats['max_val']
                gridinfo.min_val = stats['min_val']
                gridinfo.mean_val = stats['mean_val']
                gridinfo.range_vals = stats['range_vals']
                gridinfo.range_counts = stats['range_counts']

            _data = data._get_mview()    
            _data.setflags(write=1) # to resolve cython issue
            # mview array is (rows*cols,) 1D array
            # reshaping make it two dimensional without copy
            _data = np.reshape(_data,shape)

        elif isinstance(data,np.ndarray):
            if not isinstance(gridinfo,GridInfo):
                logging.error('GridInfo is not provided to write gridded dataset')
                return

            if pathname is None:
                logging.error('Provide valid pathname for grid record is invalid!',exc_info=True)
                return

            grid_type = gridinfo.grid_type
            shape = data.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata

            if gridinfo.grid_type_has_time():
                # Verify the D and E parts are valid datetime string
                pathobj = DssPathName(pathname)
                dpart = pathobj.getDPart()
                epart = pathobj.getEPart()
                try:
                    # check if dpart, epart or both are not datetime
                    # TODO: Found out HecTime('1') passes this test
                    stime = HecTime(dpart)
                    etime = HecTime(epart)
                except:
                    raise Exception('For %s grid type, DPart and EPart of pathname must be datetime string')
                else:
                    # unsure about this param
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    stime = stime._toString(end_of_day = False)
                    etime = etime._toString(end_of_day = True)
                    pathobj.setDPart(stime)
                    pathobj.setEPart(etime)
                    pathname = pathobj.text()

            _data = data
            inplace = False
            if not isinstance(data,ma.core.MaskedArray):
                # change nodata values to np.nan
                # copy occured here, so inplace modification of the copied array is ok.
                inplace = True
                _data = np.where(data==nodata,np.nan,data)

            if compute_stats:
                stats = compute_grid_stats(_data,compute_stats)
                stats['range_vals'][0] = UNDEFINED
                gridinfo.max_val = stats['max_val']
                gridinfo.min_val = stats['min_val']
                gridinfo.mean_val = stats['mean_val']
                gridinfo.range_vals = stats['range_vals']
                gridinfo.range_counts = stats['range_counts']
            
            # Check/Correct lower_left_cell and coords_cell0 parameters
            # Assumptions:
            # Albers / SHG grid
            #   • The index origin (cell (0,0)) is located at the projection origin:
            #     (false_easting, false_northing). For SHG this is (0, 0).
            #   • lower_left_cell_indices = (
            #       (minx - false_easting)  / cellsize,
            #       (miny - false_northing) / cellsize
            #     )
            #     i.e., the (col, row) of the south-west corner of the bottom-left cell, expressed in cell units.
            #
            # Specified grids
            #   • The index origin is arbitrary and depends on the chosen “origin cell.”
            #   • We follow MetVue’s convention: the bottom-left cell is the origin, so (col, row) = (0, 0).

            if gridinfo.coords_cell0 is None or gridinfo.lower_left_cell is None:
                logging.info('Updating coords_cell0 and lower_left_cell because either or both were not specified.')
                if gridinfo.grid_type == GridType.albers or gridinfo.grid_type == GridType.albers_time:
                    # coords_cell0
                    gridinfo.coords_cell0 = (0.0,0.0)
                    # lower_left_cell
                    if not gridinfo.min_xy is None:
                        gridinfo.update_albers_lower_left_cell_from_minxy()
                    elif not transform is None:
                        gridinfo.update_albers_lower_left_cell_from_transform(transform)
                    else:
                        logging.error('Provide gridinfo.min_xy or transform argument to allow calculation of lower_left_cell indices for Albers grid',exc_info=True)
                        return 

                elif gridinfo.grid_type == GridType.specified or gridinfo.grid_type == GridType.specified_time:
                    # lower_left_cell
                    gridinfo.lower_left_cell = (0,0)
                    # coords_cell0
                    if not gridinfo.min_xy is None:
                        #same as  gridinfo.update_specified_coords_cell0_from_minxy()
                        gridinfo.coords_cell0 = gridinfo.min_xy
                    elif not transform is None:
                        gridinfo.update_specified_coords_cell0_from_transform(transform)
                    else:
                        logging.error('Provide gridinfo.min_xy or transform argument to allow calculation of coords_cell0 for specified grid',exc_info=True)
                        return 

                else:
                    # TODO
                    # Hrap/Undefined GridInfo
                    gridinfo.coords_cell0 = (0.0,0.0)
                    gridinfo.lower_left_cell = (0.0,0.0)

            # Check the data array
            if isinstance(_data,ma.core.MaskedArray):
                mask = _data.mask
                _data = _data._data
            else:
                mask = np.isnan(data)

            # _data = array, mask = mask of array    
            if _data.dtype != np.float32:
                _data = _data.astype(np.float32,casting='unsafe',copy=True)
                inplace = True

            # fill np.nan with nodata value
            if inplace:
                _data[mask] = nodata
            else:
                _data = _data.astype(np.float32,casting='unsafe',copy=True)
                _data[mask] = nodata

            if flipud:
                _data = np.flipud(_data)

        if not _data.flags['C_CONTIGUOUS']:
            _data = np.ascontiguousarray(_data)

        super().put_grid(pathname, _data, gridinfo)

    #@validate_call
    def put_grid0(self, data:Union[SpatialGridStruct,np.array], pathname:Optional[PathType]=None, gridinfo:Optional[GridInfo]=None, flipud:Optional[bool]=True, compute_stats:Optional[Union[bool,List[float]]]=True, transform:Optional[Any]=None) ->None:
        """Write spatial grid to DSS-6 file. Writing to DSS-7 file not allowed.

        Parameter
        ---------
          data: numpy array or masked array or SpatialGridStruct 
             numpy array - np.nan, nodata from gridinfo are considered nodata values
             masked array - masked elements are considered nodata
          gridinfo (GridInfo for version 6 and 7):describes grid information 
          flipud: 0 or 1, flips the array
          compute_stats: bool, string or list of values
             True - compute range table using default method
             False - do not compute range table, applicable to SpatialGridStuct data only
             string - quartiles, quarters, etc., methods TODO
             list - list of values (max 19 excluding nodata) to compute equal to greater than metrics 
        """
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        if self.version == 7:
            logging.warning('Writing version 0 (DSS-6 format) grid data to DSS7 file is experimental and may cause problem')
        
        if isinstance(data, SpatialGridStruct):
            if pathname is None: pathname = data.pathname
            gridinfo7 = data.gridinfo
            grid_type = gridinfo7.grid_type
            shape = gridinfo7.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo7.nodata

            if compute_stats:
                _mdata = data.read()
                stats = compute_grid_stats(_mdata,compute_stats)
                stats['range_vals'][0] = UNDEFINED
                gridinfo7.max_val = stats['max_val']
                gridinfo7.min_val = stats['min_val']
                gridinfo7.mean_val = stats['mean_val']
                gridinfo7.range_vals = stats['range_vals']
                gridinfo7.range_counts = stats['range_counts']
            
            gridinfo6 = gridinfo7_to_gridinfo6(gridinfo7,pathname)
            _data = data._get_mview()    
            _data.setflags(write=1) 
            _data = np.reshape(_data,shape)

        elif isinstance(data,np.ndarray):
            if not isinstance(gridinfo,(GridInfo,GridInfo6)):
                logging.error('GridInfo is not provided to write gridded dataset')
                return

            if pathname is None:
                logging.error('Provide valid pathname for grid record is invalid!',exc_info=True)
                return

            # convert to gridinfo 7, which is pythonic and easy to work with
            if isinstance(gridinfo,GridInfo6):
                gridinfo = gridinfo.to_gridinfo7()

            grid_type = gridinfo.grid_type
            shape = data.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata            

            # Set alway true for DSS6 for now
            # unlike in DSS7, grid_type does not indicate the time information
            if 1 or gridinfo.grid_type_has_time():
                pathobj = DssPathName(pathname)
                dpart = pathobj.getDPart()
                epart = pathobj.getEPart()
                try:
                    stime = HecTime(dpart)
                    etime = HecTime(epart)
                except:
                    raise Exception('For %s grid type, DPart and EPart of pathname must be datetime string')
                else:
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    stime = stime._toString(end_of_day = False)
                    # 02JAN2025:0000 is changed to 01JAN2025:2400 with end_of_day = True
                    etime = etime._toString(end_of_day = True)
                    pathobj.setDPart(stime)
                    pathobj.setEPart(etime)
                    pathname = pathobj.text()

            _data = data
            inplace = False
            if not isinstance(data,ma.core.MaskedArray):
                inplace = True
                _data = np.where(data==nodata,np.nan,data)

            if compute_stats:
                stats = compute_grid_stats(_data,compute_stats)
                stats['range_vals'][0] = UNDEFINED
                gridinfo.max_val = stats['max_val']
                gridinfo.min_val = stats['min_val']
                gridinfo.mean_val = stats['mean_val']
                gridinfo.range_vals = stats['range_vals']
                gridinfo.range_counts = stats['range_counts']

            if isinstance(_data,ma.core.MaskedArray):
                mask = _data.mask
                _data = _data._data
            else:
                mask = np.isnan(data)

            if _data.dtype != np.float32:
                _data = _data.astype(np.float32,casting='unsafe',copy=True)
                inplace = True

            if inplace:
                _data[mask] = nodata
            else:
                _data = _data.astype(np.float32,casting='unsafe',copy=True)
                _data[mask] = nodata

            if flipud:
                _data = np.flipud(_data)

            if gridinfo.coords_cell0 is None or gridinfo.lower_left_cell is None:
                logging.info('Updating coords_cell0 and lower_left_cell because either or both were not specified.')
                if gridinfo.grid_type == GridType.albers or gridinfo.grid_type == GridType.albers_time:
                    # coords_cell0
                    gridinfo.coords_cell0 = (0.0,0.0)
                    # lower_left_cell
                    if not gridinfo.min_xy is None:
                        gridinfo.update_albers_lower_left_cell_from_minxy()
                    elif not transform is None:
                        gridinfo.update_albers_lower_left_cell_from_transform(transform)
                    else:
                        logging.error('Provide gridinfo.min_xy or transform argument to allow calculation of lower_left_cell indices for Albers grid',exc_info=True)
                        return 

                elif self.grid_type == GridType.specified or self.grid_type == GridType.specified_time:
                    # lower_left_cell
                    gridinfo.lower_left_cell = (0,0)
                    # coords_cell0
                    if not gridinfo.min_xy is None:
                        gridinfo.coords_cell0 = gridinfo.min_xy
                    elif not transform is None:
                        gridinfo.update_specified_coords_cell0_from_transform(transform)
                    else:
                        logging.error('Provide gridinfo.min_xy or transform argument to allow calculation of coords_cell0 for specified grid',exc_info=True)
                        return 

                else:
                    # TODO
                    # Hrap/Undefined GridInfo
                    gridinfo.coords_cell0 = (0.0,0.0)
                    gridinfo.lower_left_cell = (0.0,0.0)

            gridinfo6 = gridinfo7_to_gridinfo6(gridinfo,pathname)

        if not _data.flags['C_CONTIGUOUS']:
            _data = np.ascontiguousarray(_data)


        super().put_grid0(pathname, _data, gridinfo6)

    #@validate_call
    def copy(self,pathname_in:PathType,pathname_out:PathType,dss_out:Optional["Open"]=None) ->None:
        dss_fid = dss_out if isinstance(dss_out,self.__class__) else self
        if dss_fid.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        if (pathname_in.lower() == pathname_out.lower() or not pathname_out) and dss_fid is self:
            # overwriting with exact data is pointless
            return
        self.copyRecordsTo(dss_fid,pathname_in,pathname_out)

    #@validate_call
    def deletePathname(self,pathname:PathType) ->None:
        if self.mode != 'rw':
            logging.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        pathname = pathname.replace('//','/*/')
        pathlist = self.getPathnameList(pathname)
        for pth in pathlist:
            status = deletePathname(self,pth)

    #@validate_call
    def getPathnameList(self,pathname:PathType,sort:Optional[bool]=False) ->List[str]:
        # pathname string which can include wild card * for defining pattern
        catalog = getPathnameCatalog(self,pathname,sort)
        path_list = catalog.getPathnameList()
        return path_list

    #@validate_call
    def getPathnameDict(self) ->Dict[str,str]:
        # TODO: This does not work with DSS-6
        # This method necessary because type option in getPathnameList is not working
        path_dict = dict(zip(['TS','RTS','ITS','PD','GRID','OTHER'],
                             [[],   [],   [],   [],  [],    []]))
        path_list = self.getPathnameList('')
        for path in path_list:
            path_dict[self._record_type(path)].append(path)
        return path_dict

