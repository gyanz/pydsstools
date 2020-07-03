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
from affine import Affine

from ...core import Open as _Open
from ...core.grid import SpatialGridStruct
from ...core import getPathnameCatalog, deletePathname,PairedDataContainer,HecTime,DssPathName,dss_info
from ...heclib.utils import gridInfo,gridDataSource,computeGridStats,grid_type_names,grid_data_type_names,UNDEFINED

class Open(_Open):
    def __init__(self,dssFilename,version=None,**kwargs):
        #version = HEC-DSS version  6 or 7, automatically selected based on
        #the existing file type. When version is not specified for new file,
        # version 7 is selected.
        super().__init__(dssFilename,version)

    def read_ts(self,pathname,window=None,trim_missing=True,regular=True,window_flag=0):
        """Read time-series

        Parameter
        ---------
            pathname: string, dss record pathname

            window: tuple of start and end dates. default None
                    dates can be either python datetime object or string
                    If None, honors date or D-part of pathname.

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
            TimeSeriesStruct object

        Usage
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


    def put_ts(self,tsc,prevent_overflow=True):
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
        
        if tsc.interval > 0:
            # Regular time-series
            if not len(tsc.values) == tsc.numberValues:
                logging.error('numberValues attribute of TimeSeriesContainer not equal to length of values')
                return
            super().put(tsc)

        else:
            # Irregular time-series
            times = tsc.times
            times_copy = copy(times)
            values_copy = copy(tsc.values)
            julianbasedate = 0
            time_values = []

            if not times or not isinstance(times,(list,tuple)):
                logging.error('times for irregular time-series is not non-empty list or tuple')
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


    def read_pd(self,pathname,window=None,dtype=None,dataframe=True):
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
            if not label_list:
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

    def read_pd_labels(self,pathname):
        _df = self.read_pd(pathname,window=(1,1,1,0))
        df = pd.DataFrame(data=_df.columns,columns=['label'])
        return df

    def put_pd(self,pdc_df_array,curve_index=None,**kwargs):
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

    def preallocate_pd(self,pdc_or_shape,**kwargs):
        # Each curve is allocated 10 characters by default if label_size is not specified
        # Curves are labeled 1,2,3 ... by default
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

    def read_grid(self,pathname):
        """Read spatial grid. DSS-6 grid is returned in DSS-7 format.
        """
        sg_st = SpatialGridStruct()
        super().read_grid(pathname,sg_st)
        sg_st._get_mview() # necessary?
        return sg_st
        
    def put_grid(self, pathname, data, profile=None, flipud=1, compute_range = True, inplace = False):
        """Write spatial grid to DSS-7 file. Writing to DSS-6 file not allowed.

        Parameter
        ---------
        # data: numpy array or masked array or SpatialGridStruct 
        #    numpy array - np.nan is considered null value
        #    masked array - masked values are considered null values
        #    null value is implemention dependent 
        # profile: gridinfo dict, contains grid information; use gridInfo function   
        # flipud: 0 or 1, flips the array
        # compute_range: True/False, string or list of values
        #    True - compute range table using default method
        #    False - do not compute range table, applicable to SpatialGridStuct data only
        #    string - quartiles, quarters, etc., methods TODO
        #    list - list of values (max 19 excluding nodata) to compute equal to greater than metrics 
        """
        if self.version == 6:
            logging.warn('Writing DSS grid record in DSS-6 file is not supported')
            return

        if isinstance(data, SpatialGridStruct):
            # use this for copying from one file to another or updating statistics
            stats = data.stats
            nodata = data.nodata
            grid_info = data.profile
            if compute_range:
                _data = data.read()
                stats = computeGridStats(_data,compute_range)
                stats['range_values'][0] = nodata
            row = data.height
            col = data.width
            _data = data._get_mview()    
            _data.setflags(write=1) # to resolve cython issue
            _data = np.reshape(_data,(row,col))

        elif isinstance(data,np.ndarray):
            grid_info = profile.copy()
            nodata = UNDEFINED
            # Verify the grid parameters
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
            _opt_data_source = gridDataSource(grid_type)
            if _opt_data_source:
                logging.debug('default data source string for HRAP/SHG/Albers used')
                opt_data_source = _opt_data_source
            if not isinstance(opt_data_source,str):
                logging.debug('Empty data source string used')
                opt_data_source = ''
            grid_info['opt_data_source'] = opt_data_source


            if not isinstance(grid_info['opt_tzid'],str):
                logging.debug('Empty time zone id string used')
                grid_info['opt_tzid'] = ''

            if not isinstance(grid_info['opt_tzoffset'],int):
                logging.debug('time offset of 0 used')
                grid_info['opt_tzoffset'] = 0

            if not isinstance(grid_info['opt_crs_name'],str):
                grid_info['opt_crs_name'] = 'UNDEFINED'

            if not isinstance(grid_info['opt_crs_type'],int):
                grid_info['opt_crs_type'] = 0

            if grid_info['opt_is_interval']:
                grid_info['opt_is_interval'] = 1
            else:
                grid_info['opt_is_interval'] = 0

            if grid_info['opt_time_stamped']:
                grid_info['opt_time_stamped'] = 1
            else:
                grid_info['opt_time_stamped'] = 0

            if not compute_range: compute_range = True
            stats = computeGridStats(data,compute_range)
            stats['range_values'][0] = nodata
            print('stats=',stats)

            # Check the data array
            _data = data
            if isinstance(data,ma.core.MaskedArray):
                mask = data.mask
                _data = _data._data
            else:
                mask = np.isnan(data)

            # fill nodata value
            if inplace:
                _data[mask] = nodata
            else:
                _data = _data.copy()
                _data[mask] = nodata

            if flipud:
                _data = np.flipud(_data)


        super().put_grid(pathname, _data, nodata, stats, grid_info)

    def copy(self,pathname_in,pathname_out,dss_out=None):
        dss_fid = dss_out if isinstance(dss_out,self.__class__) else self
        if (pathname_in.lower() == pathname_out.lower() or not pathname_out) and dis_fid is self:
            # overwriting with exact data is pointless
            return
        self.copyRecordsTo(dss_fid,pathname_in,pathname_out)

    def deletePathname(self,pathname):
        pathname = pathname.replace('//','/*/')
        pathlist = self.getPathnameList(pathname)
        for pth in pathlist:
            status = deletePathname(self,pth)

    def getPathnameList(self,pathname,sort=0):
        # pathname string which can include wild card * for defining pattern
        catalog = getPathnameCatalog(self,pathname,sort)
        path_list = catalog.getPathnameList()
        return path_list

    def getPathnameDict(self):
        # This method necessary because type option in getPathnameList is not working
        path_dict = dict(zip(['TS','RTS','ITS','PD','GRID','OTHER'],
                             [[],   [],   [],   [],  [],    []]))
        path_list = self.getPathnameList('')
        for path in path_list:
            path_dict[self._record_type(path)].append(path)
        return path_dict



