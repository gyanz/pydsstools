"""
 Open class object for HEC-DSS file
"""
__all__ = ['Open']

import logging
from array import array
from datetime import datetime
import numpy as np
import pandas as pd

from ...core import Open as _Open
from ...core.grid import SpatialGridStruct
from ...core import getPathnameCatalog, deletePathname,PairedDataContainer,HecTime,DssPathName

class Open(_Open):
    def __init__(self,dssFilename,version=None):
        #version = HEC-DSS version  6 or 7, automatically selected based on
        #the existing file type. When version is not specified for new file,
        # version 7 is selected.
        super().__init__(dssFilename,version)

    def read_ts(self,pathname,window=None,datetime_format=None,trim_missing=True,regular=True,window_flag=0):
        """Read time-series

        Parameter
        ---------
            pathname: string, dss record pathname

            window: tupele of start and end dates. default None
                    dates can be either python datetime object or string
                    If None, honors date or D-part of pathname.

            datetime_format: string, default None
                             Needed if start/end date(s) is string
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


    def put_ts(self,tsc,sort_times=False):
        """Write time-series

        Parameter
        ---------
            tsc: TimeSeriesContainer

            sort_times: bool, default False
                        Sorts the data in ascending order of time element

        Returns
        --------
            None

        Usage
        ---------
            >>> ts = fid.read_ts(pathname,window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))
            >>> ts = fid.read_ts(pathname,regular=False)
        """
        if not tsc.interval > 0:
            granularity = tsc.granularity
            times = tsc.times
            count = tsc.numberValues
            if not times or not isinstance(times,(list,tuple)):
                logging.error('times for irregular time-series is not non-empty list or tuple')
                return

            if not (count == len(times)):
                logging.error('times does not have correct number of elements')
                return


            if isinstance(times[0],str):
                _times = []
                for i in range(count):
                    tm = HecTime(times[i],granularity)
                    _times.append(tm.datetimeValue)
                times = _times

            elif isinstance(times[0],datetime):
                times = [HecTime.getHecTimeFromPyDateTime(pydt,granularity).datetimeValue for pydt in times]

            elif isinstance(times[0], int):
                logging.warn('Integer value times provided will be interpreted using provided granularity.')

            else:
                logging.error('Invalid element type in times provided')
                return

            tsc.times = times

            if sort_times:
                values = tsc.values
                try:
                    values = values.tolist()
                except:
                    pass
                tm_vals = sorted(zip(times,values),key=lambda x:x[0])

                tsc.times = [t for t,v in tm_vals]
                tsc.values = [v for t,v in tm_vals]
        else:
            if not len(tsc.values) == tsc.numberValues:
                logging.error('numberValues attribute of TimeSeriesContainer not equal to length of values')
                return

        super().put(tsc)


    def read_pd(self,pathname,window=None,dtype=None):
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
                    e.g., pathname, labels_list, etc.

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
                BaseException('Unsupported data provided')
                return

            pdc_df_array = np.reshape(pdc_df_array,[1,-1])
            arr_size = pdc_df_array.size
            if not arr_size == (end_ord - start_ord + 1):
                logging.error('Incorrect size of array provided')
                return
            pdc = PairedDataContainer(pathname=pathname,labels_list=labels_list)
            pdc.curves = pdc_df_array
            super().put_one_pd(pdc,curve_index,(start_ord,end_ord))
            return

        super().put_pd(pdc)

    def preallocate_pd(self,pdc_or_shape,**kwargs):
        # Labels do not appear (bug with DSS 7?). But each curve is allocated 10 character long
        # label that can be set using put_pd method. While writing data for individual curve using put_pd
        # do not specify label data unless the paired data was created by pydsstools.
        pdc = pdc_or_shape
        if isinstance(pdc_or_shape,(list,tuple)):
            pdc = PairedDataContainer(**kwargs)
            pdc.data_no = pdc_or_shape[0]
            pdc.curve_no = pdc_or_shape[1]
            pdc.independent_axis = array('f',[i+1 for i in range(pdc.data_no)])
            if not pdc.labels_list:
                pdc.labels_list = [str(i+1) for i in range(pdc.curve_no)]

        super().prealloc_pd(pdc)

    def read_grid(self,pathname):
        sg_st = SpatialGridStruct()
        super().read_grid(pathname,sg_st)
        return sg_st

    def getPathnameList(self,pathname,sort=0):
        # pathname string which can include wild card * for defining pattern
        catalog = getPathnameCatalog(self,pathname,sort)
        path_list = catalog.getPathnameList()
        return path_list

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

