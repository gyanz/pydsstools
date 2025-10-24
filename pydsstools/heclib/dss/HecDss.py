"""
Open class object for HEC-DSS file
"""

__all__ = ["Open"]

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
import numpy.typing as npt  # npt.NDArray[np.float32], npt.Arraylike
from pydantic import validate_call
from typing import (
    Any,
    Optional,
    Union,
    Tuple,
    List,
    Dict,
    Set,
    Iterable,
    Iterator,
    Sequence,
    Mapping,
    MutableMapping,
    Callable,
    overload,
    TypedDict,
    Final,
    ClassVar,
    TypeVar,
    Generic,
    NoReturn,
)

try:
    # python 3.10+
    from typing import Annotated, TypeAlias, Literal
except:
    # 3.8 <= python < 3.10
    from typing_extensions import Annotated, TypeAlias, Literal

from ...core import Open as _Open
from ...core import TimeSeriesStruct, TimeSeriesContainer
from ...core import PairedDataStruct, PairedDataContainer
from ...core import SpatialGridStruct
from ...core.gridinfo import GridInfo, GridType
from ...core.gridv6_internals import gridinfo7_to_gridinfo6, GridInfo6
from ...core import (
    getPathnameCatalog,
    deletePathname,
    PairedDataContainer,
    HecTime,
    DssPathName,
    dss_info,
)
from ...heclib.utils import compute_grid_stats, UNDEFINED

DateLike = TypeVar("DateLike", str, datetime, HecTime)
DateWindow: TypeAlias = Tuple[DateLike, DateLike]
PathType: TypeAlias = Union[str, Path, PathLike]

def _normalize_span(start0, end0, size):
    # private helper function to convert 0-based indices to 1-based indices for paired data
    # python function expect 0-based indices while C API used 1-based indices
    if not isinstance(size, int) or size < 0:
        raise IndexError("size must be a non-negative int")
    if size == 0:
        raise IndexError("Size of the span being indexed can not be zero")

    # start (0-based, wrap negatives; must be in [0, size-1])
    if start0 is None:
        s0 = 0
    else:
        if not isinstance(start0, int):
            raise IndexError("start must be int or None")
        # wrap negative
        s0 = start0 + size if start0 < 0 else start0
        if not (0 <= s0 < size):
            raise IndexError(f"start {s0} out of range for size={size}")

    # end (0-based, wrap negatives; allow [0, size-1], clip only if >= size)
    if end0 is None:
        e0 = size - 1
    else:
        if not isinstance(end0, int):
            raise IndexError("end must be int or None")
        # wrap negative
        e0 = end0 + size if end0 < 0 else end0
        if e0 < 0:
            raise IndexError(f"end {e0} out of range after wrap")
        if e0 >= size:
            # clip
            e0 = size - 1

    if s0 > e0:
        raise IndexError(f"invalid span: start {s0} > end {e0}")

    # map 0-based to 1-based
    return (s0 + 1, e0 + 1)


class Open(_Open):
    """Open a DSS file and create a dataset object that supports input/output operations.

    This class provides an interface for reading from and writing to DSS files,
    enabling manipulation of time series, paired-data and gridded records
    contained within the file.

    """

    # @validate_call
    def __init__(
        self,
        dss_path: PathType,
        version: Optional[Literal[6, 7]] = None,
        mode: Literal["rw", "r"] = "rw",
    ) -> None:
        """
        Parameter
        ---------
        dss_path: str
            Path of the dss file.
        version: int, optional
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
        super().__init__(dss_path, version)
        self.mode = mode

    # @validate_call
    def read_ts(
        self,
        pathname: Union[str, DssPathName],
        window: Optional[DateWindow] = None,
        trim_missing: bool = False,
        window_flag: Literal[0, 1, 1, 3] = 0,
        reg: Optional[bool] = False,
        ireg: Optional[bool] = False
    ) -> TimeSeriesStruct:
        """Read time-series record

        Parameter
        ---------
        pathname: str or DssPathname
            DSS record pathname.

        window: tupe of (start, end), optional
            Time window to read. If ```None```, the date range encoded in the D-part of the ```pathname``` is used.

        trim_missing: bool,default True, applies to regular time-series only
            Removes missing values at the beginning and end of data set
        
        reg and ireg: bool, default ```False```, optional
            If reg is ``True``, treat the data as a regular time series; if ireg is ``False``, treat it as an irregular time series.
            If both are ```False``` or ```True```, the type of timeseries will be determined from E-part of ```pathname```.  

        window_flag: {0, 1, 2, 3}, default 0
            Applies to irregular time series only. Controls how the time window
            is applied:
                0
                    Strictly adhere to the time window.
                1
                    Also retrieve one value immediately before the start of the window.
                2
                    Also retrieve one value immediately after the end of the window.
                3
                    Retrieve one value immediately before the start and one immediately
                    after the end of the window.

        Returns
        --------
            TimeSeriesStruct

        Examples
        ---------
            >>> ts = fid.read_ts(pathname,window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))
            >>> ts = fid.read_ts(pathname)

        """
        pathname = DssPathName(pathname)

        infer_type = True
        if reg and ireg:
            logging.info("The timeseries to be read is specified as both regular and irregular type; type will be inferred from the pathname.")
        elif reg:
            infer_type = False
            interval = 1
        elif ireg:
            infer_type = False
            interval = -1

        if infer_type:
            # find whether the ts is regular, irregular or not ts
            logging.debug("Determining the type of timeseries record.")
            interval = self._ts_type_from_pathname(pathname.text())

            if interval == 0:
                raise ValueError("The pathname does not correspond to valid regular and irregular timeseries record. Verify E-part has standard interval.")

        if interval == 1:
            logging.debug("Reading regular time series.")
            retrieve_flag = -1 if trim_missing else 0

        else:
            logging.debug("Reading irregular time series.")
            if window_flag in [0, 1, 2, 3]:
                retrieve_flag = window_flag
            else:
                logging.error("Invalid window_flag for irregular dss record")
                return

        if window:
            start_date, end_date = window
            sdate = HecTime(start_date,midnight_as_2400=False)
            edate = HecTime(end_date,midnight_as_2400=True)
            sday = sdate.date()
            stime = sdate.time(2)
            eday = edate.date()
            etime = edate.time(2)
            return super().read_ts_window(pathname.text(), sday, stime, eday, etime, retrieve_flag)
        
        else:
            retrieve_all = 0
            if (
                not pathname.dpart.strip()
            ):  # if date part is empty, retrieve all data ignoring date
                retrieve_all = 1
            return super().read_ts_normal(
                pathname.text(), retrieve_flag, boolRetrieveAllTimes=retrieve_all
            )


    # @validate_call
    def put_ts(
        self, data: Union[str, "DssPathName","TimeSeriesContainer"],
        **kwargs: Any
    ) -> None:
        """Write time-series data.

        Parameter
        ---------
            data: pathname or TimeSeriesContainer
            kwargs: keyword arguments for TimeSeriesContainer when data is pathname

        Returns
        --------
            None

        Usage
        ---------
            >>> from pydsstools.heclib.dss.HecDss import Open
            >>> from pydsstools.core import TimeSeriesContainer
            >>> fid = Open("dss_file.dss",mode="rw")
            >>> pathname = r"/A/B/C//1HOUR/F/" 
            >>> values = [10,20,30,40,50]
            >>> interval = 1
            >>> start_time = r"01JAN2025 1500"
            >>> data_units = "ft"
            >>> data_type = "inst"
            >>> timezone = "UTC"  
            >>> tsc = TimeSeriesContainer(pathname,len(values),interval,values=values,start_time=start_time,data_units=data_units,data_type=data_type,tzid=timezone)
            >>> fid.put_ts(tsc)

            Write timeseries data (e.g., irregular timeseries) without using TimeSeries Container. Timeseries type is inferred from E-part.
            >>> pathname = r"/A/B/C//IR-DAY/F/"
            >>> julian_base = "01JAN2000"
            >>> times =  ["02JUL2010 1200", "05JAN2012 0000", "15MAR2014 0200", "25FEB2018 0500", "19DEC2024 1200"]
            >>> values = [1,20,30,40,50]
            >>> fid.put_ts(pathname,values=values,times=times,julian_base=julian_base,data_units=data_units,data_type=data_type,yzid=timezone)
        """

        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if not isinstance(data,(str,DssPathName,TimeSeriesContainer)):
            raise TypeError(f"Expected pathname or TimeSeriesContainer, got {type(data).__name__}.")

        if isinstance(data,TimeSeriesContainer):
            tsc = data
            if tsc.interval > 0:
                # Regular time-series
                if not tsc.start_time:
                    raise ValueError("Start date/time for regular timeseries container is not provided")

            else:
                # Irregular time-series
                if tsc.times is None:
                    raise ValueError("Times for regular irregular timeseries container is not provided")

            if tsc.values is None:
                raise ValueError("Values for timeseries container is not provided")
        
        else:
            pathname = DssPathName(data)
            if "pathname" in kwargs:
                logging.warning("Ignorning pathname for TimeSeriesContainer provided as keyword argument")

            # -1 = irregular
            #  1 = regular
            #  0 = invalid
            interval = self._ts_type_from_pathname(pathname.text())
            if interval == 0:
                raise ValueError("The pathname for timeseries has invalid interval information")
            
            values = kwargs["values"]
            count = len(values)
            _count = kwargs.pop("count",None)

            if _count is not None:  # noqa: SIM102
                if _count != count:
                    logging.warning(f"Ignoring count argument value (={_count}) as it is not equal to the length of values (={count})")

            if interval < 0:
                # required for irregular time-series
                times = kwargs["times"]

            tsc = TimeSeriesContainer(pathname.text(),count,interval,**kwargs)

        super().put(tsc)

    # @validate_call
    def read_pd(
        self,
        pathname: Union[str, "DssPathName"],
        window: Optional[DateWindow] = None,
        dataframe: Optional[bool] = True,
    ) -> pd.DataFrame:
        """Read paired data.

        Parameter
        ---------
            pathname : str or DssPathName
                DSS record pathname.

            window : tuple[int, int, int, int], optional
                Index window to read. If ``None``, all rows and columns are read.

                Supported forms:
                    - ``(row_start, row_end, col_start, col_end)``

                Indexing rules:
                    - Zero-based and **inclusive at both ends**.
                    - ``row_start`` / ``col_start`` ≥ 0 (first row/column is 0).
                    - ``row_end`` / ``col_end`` ≤ last valid index.
                    - ``None`` for any bound selects the respective first/last index.
                    - Negative indices are allowed (Python-style) and are **wrapped**.
                    - If an **end** index overflows the table size, it is **clipped**.
                    - Any other out-of-range condition raises ``IndexError``.

                dataframe : bool, default True
                    If ``True``, return a pandas DataFrame.
                    If ``False``, return a PairedDataStruct object.
        Returns
        -------
        pandas.DataFrame or PairedDataStruct
            Paired data in the requested format.

        Usage
        ---------
            >>> fid.read_pd(pathname,window=(2,5))
            >>> fid.read_pd(pathname)
        """
        pathname = DssPathName(pathname)

        if window:
            logging.debug(f"Input paired data window = '{window}'")
            size_info = self.pd_info(pathname.text())
            rows = size_info["data_no"]
            cols = size_info["curve_no"]
            # user's 0-based indices
            _row_start, _row_end, _col_start, _col_end = window

            row_start, row_end = _normalize_span(_row_start,_row_end,rows)
            col_start, col_end = _normalize_span(_col_start,_col_end,cols)

            window = (row_start, row_end, col_start, col_end)

            # updated zero based indices
            _row_start, _row_end, _col_start, _col_end = [x-1 for x in window]

            logging.debug(f"Updated window = '{window}'")

        pds = super().read_pd(pathname.text(), window)

        if dataframe:
            x_data = pds.x_data
            y_data = pds.y_data
            y_labels = pds.y_labels
            logging.debug(y_labels)
            # The row in curves array contains curve data
            # Transpose causes the curve data to be in columns (for DataFrame purpose)
            tb = np.asarray(y_data).T
            if not window:
                _col_start = 0
                _col_end = tb.shape[1]-1

            primary_colnames = [f"y{i}" for i in range(_col_start,_col_end+1)]
            alias_colnames = ['' for x in range(_col_start,_col_end+1)]

            logging.debug(f'window:{window}')
            logging.debug(f'col_start/end: {_col_start},{_col_end}')
            logging.debug(f'primary colnames: {primary_colnames}')
            logging.debug(f'alias columns: {alias_colnames}')

            for i,label in enumerate(y_labels):
                alias_colnames[i] = label

            logging.debug(f'Revised alias columns: {alias_colnames}')
            column_names = pd.MultiIndex.from_arrays([primary_colnames, alias_colnames], names=["primary", "labels"]) 

            indx = list(x_data[0])
            df = pd.DataFrame(
                data=tb, index=indx, columns=column_names, copy=True
            )
            df.index.name = "x_data"
            return df

        return pds

    # @validate_call
    def read_pd_labels(self, pathname: Union[str, "DssPathName"]):
        pathname = DssPathName(pathname)
        _df = self.read_pd(pathname.text(), window=(0, 0, 0, None))
        label0 = _df.columns.get_level_values(0).tolist()
        label1 = _df.columns.get_level_values(1).tolist()
        return dict(zip(label0,label1))

    # @validate_call
    def put_pd(
        self,
        data: Union["PairedDataContainer", str, "DssPathName"],
        **kwargs: Any,
    ) -> None:
        """ Write new paired data or edit an existing paired data record in the DSS file.

        Parameters
        ----------
        data : PairedDataContainer,  str, or DssPathName
            Input data to write. Can be:
                - A PairedDataContainer object.
                - A string or DssPathName specifying an existing or new DSS record pathname.

        **kwargs : Any
            Additional keyword arguments or attributes for the PairedDataContainer.

        Returns
        -------
        None
            This method does not return a value.

        Usage
        ---------
            Write PairedDataContainer 
            >>> from pydsstools.core import PairedDataContainer
            >>> pathname = "/A/B/STAGE-FLOW/D/E/F/"
            >>> curves = 2
            >>> rows = 5
            >>> pdc = PairedDataContainer(pathname,(rows,curves))
            >>> pdc.x_data = [0.1,0.2,0.3,0.4,0.5] 
            >>> pdc.y_data = [[10,20,30,40,50],[1,2,3,4,5]]
            >>> pdc.x_units = "ft" 
            >>> pdc.x_type = "linear" 
            >>> pdc.y_units = "cfs" 
            >>> pdc.y_type = "linear"
            >>> fid.put_pd(pdc) 

            Write dataframe
            >>> import pandas as pd
            >>> pathname = "/A/B/STAGE-FLOW/D/E/F/"
            >>> df = pd.DataFrame({"Curve #1":[1,2],"Curve #2":[3,4]},index=[0.5,0.6]) 
            >>> fid.put_pd(pathname,x_units="ft",x_type="linear",y_data=df,y_units="cfs",y_type="linear")

            Write a curve to preallocated paired data record
            >>> pathname = "/A/B/STAGE-FLOW/D/E/PREALLOC/"
            >>> fid.put_pd(pathname,col_index=2,y_data=[1,2,3,4],window=(2,5))

        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if isinstance(data,PairedDataContainer):
            super().put_pd(data)
            return

        if isinstance(data, (str,DssPathName)):
            pathname = DssPathName(data)
            y_data = kwargs.pop("y_data",None)
            col_index = kwargs.pop("col_index")

            if "pathname" in kwargs:
                logging.warning("Ignorning pathname for TimeSeriesContainer provided as keyword argument")

            if isinstance(y_data, pd.DataFrame):
                logging.info('Writing paired data from DataFrame')
                df = y_data
                shape = df.shape

                pdc = PairedDataContainer(pathname.text(),shape,**kwargs)
                pdc.x_data = df.index.values
                pdc.y_data = df.values.T
                y_labels = [x.strip() for x in df.columns.tolist()]

                # TODO: check for multilevel index explicitly
                try:
                    # if the column index is multilevel and contains level named 'labels'
                    y_labels = df.columns.get_level_values('labels').tolist()
                    y_labels = [x.strip() for x in y_labels]
                except:
                    pass

                pdc.y_labels = y_labels
                super().put_pd(pdc)
                return

            elif isinstance(col_index, int):
                logging.info('Writing single paired data curve to preallocated pairedata set')
                # pd_info raise error if the record does not exist
                size_info = self.pd_info(pathname.text())
                rows = size_info["data_no"]
                cols = size_info["curve_no"]
                logging.debug(f"The paired data record ({pathname.text()}) in file has rows={rows} and cols={cols}")
                
                # 1-based col_index
                logging.debug(f"Input 0-based col_index = {col_index}")
                col_index,_ = _normalize_span(col_index,None,cols)
                logging.debug(f"Updated 1-based col_index = {col_index}")

                # 1-based default indices
                row_start, row_end = (1, rows)
                logging.debug(f"1-based (row_start,row_end) assuming full curve data is replaced: ({row_start},{row_end}.")

                # update indices based on input
                window = kwargs.pop("window", None)
                if window:
                    if not isinstance(window, (tuple,list)):
                        raise ValueError("The window for writing single paired data must be tuple/list containing start and end row indices.")

                    if len(window) < 2:
                        raise ValueError(f"The window for writing single paired data curve must contain two integers; provided '{window}'.")

                    elif len(window) > 2:
                        window = window[0:2]

                    # 0-based
                    _row_start, _row_end = window
                    logging.debug(f"0-based (row_start,row_end) provided as input: ({_row_start},{_row_end}.")
                    # 1-based
                    row_start, row_end = _normalize_span(_row_start,_row_end,rows)
                    logging.debug(f"1-based (row_start,row_end) derived from input: ({row_start},{row_end}.")

                y_labels = kwargs.pop('y_labels',[])

                # Verify y_data has ndim == 1, or if ndim == 1 shape[0] == 1
                _y_data = y_data
                if isinstance(y_data,(tuple,list)):
                    _y_data = np.array(y_data,np.float32)
                
                if not isinstance(_y_data,np.ndarray):
                    raise TypeError("y_data for paired data is not of valid type")
                
                if _y_data.ndim > 2:
                    raise ValueError("The dimension of y_data should be 1 or 2.")

                if _y_data.ndim == 1:
                    _y_data = np.ascontiguousarray(_y_data.reshape(1,-1))

                if _y_data.ndim == 2 and _y_data.shape[0] != 1:
                    logging.warning("The y_data for single curve has multiple rows; flattening the data as single row of values.")
                    _y_data = np.ascontiguousarray(_y_data.reshape(1,-1))
                
                y_data = _y_data

                shape = (y_data.shape[1],1)

                if shape[0] + row_start - 1 > rows:
                    raise IndexError("y_data has too many values exceeding allowable row_end index")
                
                # update  row_end based on number of y_data values 
                if row_end != row_start + shape[0] - 1:
                    logging.debug("row_end updated based on the number of y_data")
                    row_end = row_start + shape[0] - 1

                logging.debug(f"Single paired data curve to be written with 1-based row_start={row_start} and row_end={row_end}. Total rows in dss = {rows}.")
                pdc = PairedDataContainer(pathname.text(),shape, 
                                        y_data=y_data,
                                        x_data=None,
                                        x_units=None,
                                        x_type=None,
                                        y_units=None,
                                        y_type=None,
                                        y_labels = y_labels,
                                        )

                super().put_one_pd(pdc, col_index, (row_start, row_end))
                return
        
        raise ValueError('Incompatible input parameters provided to write paired data to dss file')


    # @validate_call
    def preallocate_pd(
        self,
        pathname: Union[str, "DssPathName"],
        shape: Union[List[int],Tuple[int]],
        **kwargs: Any,
    ) -> None:
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return
        
        pathname = DssPathName(pathname)
        pdc = PairedDataContainer(pathname.text(), shape, **kwargs)
        super().prealloc_pd(pdc)

    # @validate_call
    def read_grid(
        self, pathname: Union[str, "DssPathName"], metadata_only: Optional[bool] = False
    ) -> SpatialGridStruct:
        """Reads both version 0 (DSS-6 format) and 100 (latest DSS-7 format) spatial grid data from dss file.

        Returns SpatialGridStruct object.
        """
        pathname = DssPathName(pathname)
        sg_st = SpatialGridStruct()
        retrieve_data = False if metadata_only else True
        # super().read_grid(pathname,sg_st,retrieve_data)
        grid_ver = self._get_gridver(pathname.text())

        if grid_ver is None:
            logging.error("Invalid grid data or version")
            return

        elif grid_ver == 100:
            logging.info("Reading modern format (DSS7) grid")
            super().read_grid100(pathname.text(), sg_st, retrieve_data)

        else:
            logging.info(
                "Read grid version {} and convert it to version 100 grid".format(
                    grid_ver
                )
            )
            # find grid_type and create info6
            grid_type = self._get_gridtype(pathname.text())
            logging.debug("grid type is {}".format(grid_type))
            info6 = GridInfo6.from_grid_type(grid_type)
            logging.debug("grid type in info6 is {}".format(info6.grid_type))
            if grid_type == 430:
                # add space for crs defination, tz id generously
                # it should be more than what is in the file
                info6 = GridInfo6.get_specinfo6(50, 200, 50)
                logging.debug(
                    "grid type in updated info6 is {}".format(info6.grid_type)
                )
            super().read_grid0(pathname.text(), sg_st, info6, retrieve_data)

        return sg_st

    def read_grid2(
        self, pathname: Union[str, "DssPathName"], metadata_only: Optional[bool] = False
    ) -> Optional[tuple]:
        """Reads both version 0 (DSS-6 format) and 100 (latest DSS-7 format) spatial grid data.

        Returns a tuple consisting of np.array and gridinfo.
        """
        pathname = DssPathName(pathname)
        retrieve_data = False if metadata_only else True
        grid_ver = self._get_gridver(pathname.text())
        if grid_ver is None:
            logging.error("Invalid grid data or version")
        elif grid_ver != 0:
            logging.info("Reading modern format (DSS7) grid")
            ds = self.read_grid(pathname.text(), retrieve_data)
            if metadata_only:
                logging.info("Returning metadata of gridded data")
                return ds.gridinfo
            else:
                return ds.read(), ds.gridinfo
        else:
            logging.info("Reading older format (DSS6 or grid version 0) grid")
            # find grid_type and create info6
            grid_type = self._get_gridtype(pathname.text())
            info6 = GridInfo6.from_grid_type(grid_type)
            if grid_type == 430:
                # add space for crs defination, tz id generously
                # it should be more than what is in the file
                info6 = GridInfo6.get_specinfo6(50, 200, 50)
            # info6 is updated with data from the dss file
            data = super()._read_grid0_array(pathname.text(), info6, retrieve_data)
            if metadata_only:
                logging.info("Returning metadata of gridded data")
                if data is not None:
                    return info6
            if data is not None:
                logging.info("Returning metadata/data of gridded data")
                return data, info6

    # @validate_call
    def put_grid(
        self,
        data: Union["SpatialGridStruct", "np.array"],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[GridInfo] = None,
        flipud: Optional[bool] = True,
        compute_stats: Optional[Union[bool, List[float]]] = True,
        transform: Optional[Any] = None,
    ) -> None:
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

        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 6:
            logging.warning("Writing DSS grid record in DSS-6 file is not supported")
            return

        if isinstance(data, SpatialGridStruct):
            # use this for copying from one file to another or updating statistics
            if pathname is None:
                pathname = DssPathName(data.pathname)
            else:
                pathname = DssPathName(pathname)

            gridinfo = data.gridinfo
            grid_type = gridinfo.grid_type
            shape = gridinfo.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata

            if compute_stats:
                # nodata is taken care within read method to give masked data
                _mdata = data.read()
                stats = compute_grid_stats(_mdata, compute_stats)
                stats["range_vals"][0] = UNDEFINED
                gridinfo.max_val = stats["max_val"]
                gridinfo.min_val = stats["min_val"]
                gridinfo.mean_val = stats["mean_val"]
                gridinfo.range_vals = stats["range_vals"]
                gridinfo.range_counts = stats["range_counts"]

            _data = data._get_mview()
            _data.setflags(write=1)  # to resolve cython issue
            # mview array is (rows*cols,) 1D array
            # reshaping make it two dimensional without copy
            _data = np.reshape(_data, shape)

        elif isinstance(data, np.ndarray):
            if not isinstance(gridinfo, GridInfo):
                logging.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logging.error(
                    "Provide valid pathname for grid record is invalid!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)
            grid_type = gridinfo.grid_type
            shape = data.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata

            if gridinfo.grid_type_has_time():
                # Verify the D and E parts are valid datetime string
                dpart = pathname.dpart
                epart = pathname.epart
                try:
                    # check if dpart, epart or both are not datetime
                    # TODO: Found out HecTime('1') passes this test
                    stime = HecTime(dpart,midnight_as_2400 = False)
                    etime = HecTime(epart,midnight_as_2400 = True)
                except:
                    raise Exception(
                        "For %s grid type, DPart and EPart of pathname must be datetime string"
                    )
                else:
                    # unsure about this param
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    pathname.dpart = stime
                    pathname.epart = etime

            _data = data
            inplace = False
            if not isinstance(data, ma.core.MaskedArray):
                # change nodata values to np.nan
                # copy occured here, so inplace modification of the copied array is ok.
                inplace = True
                _data = np.where(data == nodata, np.nan, data)

            if compute_stats:
                stats = compute_grid_stats(_data, compute_stats)
                stats["range_vals"][0] = UNDEFINED
                gridinfo.max_val = stats["max_val"]
                gridinfo.min_val = stats["min_val"]
                gridinfo.mean_val = stats["mean_val"]
                gridinfo.range_vals = stats["range_vals"]
                gridinfo.range_counts = stats["range_counts"]

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
                logging.info(
                    "Updating coords_cell0 and lower_left_cell because either or both were not specified."
                )
                if (
                    gridinfo.grid_type == GridType.albers
                    or gridinfo.grid_type == GridType.albers_time
                ):
                    # coords_cell0
                    gridinfo.coords_cell0 = (0.0, 0.0)
                    # lower_left_cell
                    if gridinfo.min_xy is not None:
                        gridinfo.update_albers_lower_left_cell_from_minxy()
                    elif transform is not None:
                        gridinfo.update_albers_lower_left_cell_from_transform(transform)
                    else:
                        logging.error(
                            "Provide gridinfo.min_xy or transform argument to allow calculation of lower_left_cell indices for Albers grid",
                            exc_info=True,
                        )
                        return

                elif (
                    gridinfo.grid_type == GridType.specified
                    or gridinfo.grid_type == GridType.specified_time
                ):
                    # lower_left_cell
                    gridinfo.lower_left_cell = (0, 0)
                    # coords_cell0
                    if gridinfo.min_xy is not None:
                        # same as  gridinfo.update_specified_coords_cell0_from_minxy()
                        gridinfo.coords_cell0 = gridinfo.min_xy
                    elif not transform is None:
                        gridinfo.update_specified_coords_cell0_from_transform(transform)
                    else:
                        logging.error(
                            "Provide gridinfo.min_xy or transform argument to allow calculation of coords_cell0 for specified grid",
                            exc_info=True,
                        )
                        return

                else:
                    # TODO
                    # Hrap/Undefined GridInfo
                    gridinfo.coords_cell0 = (0.0, 0.0)
                    gridinfo.lower_left_cell = (0.0, 0.0)

            # Check the data array
            if isinstance(_data, ma.core.MaskedArray):
                mask = _data.mask
                _data = _data._data
            else:
                mask = np.isnan(data)

            # _data = array, mask = mask of array
            if _data.dtype != np.float32:
                _data = _data.astype(np.float32, casting="unsafe", copy=True)
                inplace = True

            # fill np.nan with nodata value
            if inplace:
                _data[mask] = nodata
            else:
                _data = _data.astype(np.float32, casting="unsafe", copy=True)
                _data[mask] = nodata

            if flipud:
                _data = np.flipud(_data)

        if not _data.flags["C_CONTIGUOUS"]:
            _data = np.ascontiguousarray(_data)

        super().put_grid(pathname.text(), _data, gridinfo)

    # @validate_call
    def put_grid0(
        self,
        data: Union["SpatialGridStruct", "np.array"],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[GridInfo] = None,
        flipud: Optional[bool] = True,
        compute_stats: Optional[Union[bool, List[float]]] = True,
        transform: Optional[Any] = None,
    ) -> None:
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
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 7:
            logging.warning(
                "Writing version 0 (DSS-6 format) grid data to DSS7 file is experimental and may cause problem"
            )

        if isinstance(data, SpatialGridStruct):
            if pathname is None:
                pathname = DssPathName(data.pathname)
            else:
                pathname = DssPathName(pathname)

            gridinfo7 = data.gridinfo
            grid_type = gridinfo7.grid_type
            shape = gridinfo7.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo7.nodata

            if compute_stats:
                _mdata = data.read()
                stats = compute_grid_stats(_mdata, compute_stats)
                stats["range_vals"][0] = UNDEFINED
                gridinfo7.max_val = stats["max_val"]
                gridinfo7.min_val = stats["min_val"]
                gridinfo7.mean_val = stats["mean_val"]
                gridinfo7.range_vals = stats["range_vals"]
                gridinfo7.range_counts = stats["range_counts"]

            gridinfo6 = gridinfo7_to_gridinfo6(gridinfo7, pathname)
            _data = data._get_mview()
            _data.setflags(write=1)
            _data = np.reshape(_data, shape)

        elif isinstance(data, np.ndarray):
            if not isinstance(gridinfo, (GridInfo, GridInfo6)):
                logging.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logging.error(
                    "Provide valid pathname for grid record is invalid!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)

            # convert to gridinfo 7, which is pythonic and easy to work with
            if isinstance(gridinfo, GridInfo6):
                gridinfo = gridinfo.to_gridinfo7()

            grid_type = gridinfo.grid_type
            shape = data.shape
            nodata = UNDEFINED
            if grid_type == GridType.specified or grid_type == grid_type.specified_time:
                nodata = gridinfo.nodata

            # Set alway true for DSS6 for now
            # unlike in DSS7, grid_type does not indicate the time information
            if 1 or gridinfo.grid_type_has_time():
                dpart = pathname.dpart
                epart = pathname.epart
                try:
                    stime = HecTime(dpart,midnight_as_2400=False)
                    etime = HecTime(epart,midnight_as_2400=True)
                except:
                    raise Exception(
                        "For %s grid type, DPart and EPart of pathname must be datetime string"
                    )
                else:
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    pathname.dpart = stime
                    pathname.epart = etime

            _data = data
            inplace = False
            if not isinstance(data, ma.core.MaskedArray):
                inplace = True
                _data = np.where(data == nodata, np.nan, data)

            if compute_stats:
                stats = compute_grid_stats(_data, compute_stats)
                stats["range_vals"][0] = UNDEFINED
                gridinfo.max_val = stats["max_val"]
                gridinfo.min_val = stats["min_val"]
                gridinfo.mean_val = stats["mean_val"]
                gridinfo.range_vals = stats["range_vals"]
                gridinfo.range_counts = stats["range_counts"]

            if isinstance(_data, ma.core.MaskedArray):
                mask = _data.mask
                _data = _data._data
            else:
                mask = np.isnan(data)

            if _data.dtype != np.float32:
                _data = _data.astype(np.float32, casting="unsafe", copy=True)
                inplace = True

            if inplace:
                _data[mask] = nodata
            else:
                _data = _data.astype(np.float32, casting="unsafe", copy=True)
                _data[mask] = nodata

            if flipud:
                _data = np.flipud(_data)

            if gridinfo.coords_cell0 is None or gridinfo.lower_left_cell is None:
                logging.info(
                    "Updating coords_cell0 and lower_left_cell because either or both were not specified."
                )
                if (
                    gridinfo.grid_type == GridType.albers
                    or gridinfo.grid_type == GridType.albers_time
                ):
                    # coords_cell0
                    gridinfo.coords_cell0 = (0.0, 0.0)
                    # lower_left_cell
                    if not gridinfo.min_xy is None:
                        gridinfo.update_albers_lower_left_cell_from_minxy()
                    elif not transform is None:
                        gridinfo.update_albers_lower_left_cell_from_transform(transform)
                    else:
                        logging.error(
                            "Provide gridinfo.min_xy or transform argument to allow calculation of lower_left_cell indices for Albers grid",
                            exc_info=True,
                        )
                        return

                elif (
                    self.grid_type == GridType.specified
                    or self.grid_type == GridType.specified_time
                ):
                    # lower_left_cell
                    gridinfo.lower_left_cell = (0, 0)
                    # coords_cell0
                    if not gridinfo.min_xy is None:
                        gridinfo.coords_cell0 = gridinfo.min_xy
                    elif not transform is None:
                        gridinfo.update_specified_coords_cell0_from_transform(transform)
                    else:
                        logging.error(
                            "Provide gridinfo.min_xy or transform argument to allow calculation of coords_cell0 for specified grid",
                            exc_info=True,
                        )
                        return

                else:
                    # TODO
                    # Hrap/Undefined GridInfo
                    gridinfo.coords_cell0 = (0.0, 0.0)
                    gridinfo.lower_left_cell = (0.0, 0.0)

            gridinfo6 = gridinfo7_to_gridinfo6(gridinfo, pathname.text())

        if not _data.flags["C_CONTIGUOUS"]:
            _data = np.ascontiguousarray(_data)

        super().put_grid0(pathname.text(), _data, gridinfo6)

    # @validate_call
    def copy(
        self,
        pathname_in: Union[str, "DssPathName"],
        pathname_out: Union[str, "DssPathName"],
        dss_out: Optional["Open"] = None,
    ) -> None:
        dss_fid = dss_out if isinstance(dss_out, self.__class__) else self
        if dss_fid.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return
        
        pathname_in = DssPathName(pathname_in)
        pathname_out = DssPathName(pathname_out)

        if (
            pathname_in.text().lower() == pathname_out.text().lower()
        ) and dss_fid is self:
            # overwriting with exact data is pointless
            return
        self.copyRecordsTo(dss_fid, pathname_in.text(), pathname_out.text())

    # @validate_call
    def del_path(self, pathname: Union[str, "DssPathName"]) -> None:
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname = DssPathName(pathname)
        pathname = pathname.text()
        pathname = pathname.replace("//", "/*/")
        pathlist = self.getPathnameList(pathname)
        for pth in pathlist:
            status = deletePathname(self, pth)

    # @validate_call
    def search_path(
        self, pathname: Union[str, "DssPathName"], sort: Optional[bool] = False
    ) -> List[str]:
        # pathname string which can include wild card * for defining pattern
        pathname = DssPathName(pathname)
        catalog = getPathnameCatalog(self, pathname.text(), sort)
        path_list = catalog.getPathnameList()
        return path_list

    # @validate_call
    def path_dict(self) -> Dict[str, str]:
        # TODO: This does not work with DSS-6
        # This method necessary because type option in getPathnameList is not working
        path_dict = dict(
            zip(["TS", "RTS", "ITS", "PD", "GRID", "OTHER"], [[], [], [], [], [], []])
        )
        path_list = self.getPathnameList("")
        for path in path_list:
            path_dict[self._record_type(path)].append(path)
        return path_dict
