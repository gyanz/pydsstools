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
        super().__init__(dss_path, version)
        self.mode = mode

    # @validate_call
    def read_ts(
        self,
        pathname: Union[str, Path, PathLike],
        window: Optional[DateWindow] = None,
        trim_missing: bool = False,
        regular: bool = True,
        window_flag: Literal[0, 1, 1, 3] = 0,
    ) -> TimeSeriesStruct:
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
        retrieve_flag = 0  # adhere to window

        if regular:
            retrieve_flag = -1 if trim_missing else retrieve_flag

        else:
            if window_flag in [0, 1, 2, 3]:
                retrieve_flag = window_flag
            else:
                logging.error("Invalid window_flag for irregular dss record")
                return

        if not window:
            pathobj = DssPathName(pathname)
            retrieve_all = 0
            if (
                not pathobj.getDPart().strip()
            ):  # if date part is empty, retrieve all data ignoring date
                retrieve_all = 1
            return super().read_path(
                pathname, retrieve_flag, boolRetrieveAllTimes=retrieve_all
            )

        start_date, end_date = window
        sdate = HecTime(start_date)
        edate = HecTime(end_date,midnight_as_2400=True)
        #if isinstance(startdate, str):
        #    startdate = HecTime.getPyDateTimeFromString(startdate)
        #elif not isinstance(startdate, datetime):
        #    logging.error("startdate is not string or datetime object")
        #    return

        #if isinstance(enddate, str):
        #    enddate = HecTime.getPyDateTimeFromString(enddate)
        #elif not isinstance(enddate, datetime):
        #    logging.error("enddate is not string or datetime object")
        #    return

        #sday = startdate.strftime("%d%b%Y")
        #stime = startdate.strftime("%H:%M:%S")
        #eday = enddate.strftime("%d%b%Y")
        #etime = enddate.strftime("%H:%M:%S")
        sday = sdate.date()
        stime = sdate.time(2)
        eday = edate.date()
        etime = edate.time(2)

        return super().read_window(pathname, sday, stime, eday, etime, retrieve_flag)

    # @validate_call
    def put_ts(
        self, tsc: "TimeSeriesContainer",
        **kwargs: Any
    ) -> None:
        """Write time-series

        Parameter
        ---------
            tsc: TimeSeriesContainer

        Returns
        --------
            None

        Usage
        ---------
            >>> ts = fid.read_ts(pathname,window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))
            >>> ts = fid.read_ts(pathname,regular=False)
        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if isinstance(tsc,TimeSeriesContainer):
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

        super().put(tsc)

    # @validate_call
    def read_pd(
        self,
        pathname: PathType,
        window: Optional[DateWindow] = None,
        dtype: Optional["np.dtype"] = None,
        dataframe: Optional[bool] = True,
    ) -> pd.DataFrame:
        """Read paired data as pandas dataframe

        Parameter
        ---------
            pathname: string, dss record pathname

            window: tuple, default None
                    tuple of (starting row, ending row, starting column, ending column) indices.
                    If None, read all data.
                    starting row, starting curve >= 0, i.e., first row or column is 0, not 1.
                    ending row, ending column < total rows/columns in paired data
                    #0 can be used to specify last row or curve. Negative number works like indexing of python list.

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
            #total_ordinates = size_info["data_no"]
            #total_curves = size_info["curve_no"]
            rows = size_info["data_no"]
            cols = size_info["curve_no"]
            row_start, row_end, col_start, col_end = window
            if row_end < 0:
                row_end = rows + row_end
            if col_end < 0:
                col_end = cols + col_end
            if not (
                row_start >= 0 and row_end < rows and row_end >= row_start
            ):
                logging.error("Row indices in window for paired data are out of bounds")
                return
            if not (
                col_start >= 0
                and col_end < cols
                and col_end >= col_start
            ):
                logging.error("Column indices of window for paired data are out of bounds")
                return
            window = (row_start, row_end, col_start, col_end)

        pds = super().read_pd(pathname, window)

        if dataframe:
            #x, curves, label_list = pds.get_data()
            x_data = pds.x_data
            y_data = pds.y_data
            y_labels = pds.y_labels
            logging.debug(y_labels)
            # The row in curves array contains curve data
            # Transpose causes the curve data to be in columns (for DataFrame purpose)
            tb = np.asarray(y_data).T
            if not window:
                col_start = 0
                col_end = tb.shape[1]-1

            primary_colnames = [f"y{i}" for i in range(col_start,col_end+1)]
            alias_colnames = ['' for x in range(col_start,col_end+1)]

            logging.debug(f'window:{window}')
            logging.debug(f'col_start/end: {col_start},{col_end}')
            logging.debug(f'primary colnames: {primary_colnames}')
            logging.debug(f'alias columns: {alias_colnames}')

            for i,label in enumerate(y_labels):
                alias_colnames[i] = label

            logging.debug(f'Revised alias columns: {alias_colnames}')
            column_names = pd.MultiIndex.from_arrays([primary_colnames, alias_colnames], names=["primary", "labels"]) 

            indx = list(x_data[0])
            df = pd.DataFrame(
                data=tb, index=indx, columns=column_names, dtype=dtype, copy=True
            )
            df.index.name = "x_data"
            return df
        else:
            return pds

    # @validate_call
    def read_pd_labels(self, pathname: PathType):
        _df = self.read_pd(pathname, window=(1, 1, 1, 0))
        df = pd.DataFrame(data=_df.columns, columns=["label"])
        return df

    # @validate_call
    def put_pd(
        self,
        pdc_df_array: Union["PairedDataContainer", "pd.DataFrame", "np.ndarray"],
        **kwargs: Any,
    ) -> None:
        """Write paired new or edit existing data series

        Parameter
        ---------
            pdc_df_array: PairedDataContainer, pandas dataframe or numpy array
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
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        col_index = kwargs.pop("col_index",None)
        if isinstance(pdc_df_array,PairedDataContainer):
            super().put_pd(pdc_df_array)

        if isinstance(pdc_df_array, pd.DataFrame):
            logging.info('Writing paired data from DataFrame')
            df = pdc_df_array
            pathname = kwargs.pop("pathname")
            shape = df.shape

            pdc = PairedDataContainer(pathname,shape,**kwargs)
            pdc.x_data = df.index.values
            pdc.y_data = df.values.T
            y_labels = [x.strip() for x in df.columns.tolist()]
            try:
                # if the column index is multilevel and contains level named 'labels'
                y_labels = df.columns.get_level_values('labels').tolist()
                y_labels = [x.strip() for x in y_labels]
            except:
                pass

            pdc.y_labels = y_labels
            super().put_pd(pdc)

        elif col_index is not None:
            logging.info('Writing specific paired data curve to preallocated pairedata set')
            y_data = pdc_df_array
            pathname = kwargs.pop("pathname")
            window = kwargs.pop("window", None)
            labels = kwargs.get("y_labels", [])
            size_info = self.pd_info(pathname)
            rows = size_info["data_no"]
            cols = size_info["curve_no"]

            row_start, row_end = (0, rows-1)
            if window:
                row_start, row_end = window
                if row_end < 0:
                    row_end = rows + row_end
                if not (
                    row_start >= 0
                    and row_end < rows
                    and row_end >= row_start
                ):
                    logging.error("Ordinate indices of window out of bounds")
                    return

            if kwargs.pop('y_data',None) is not None:
                raise ValueError('Duplicate entry of y_data for paired data')

            x_data = kwargs.pop('x_data')
            x_units = kwargs.pop('x_units','')
            x_type = kwargs.pop('x_type','linear')
            y_units = kwargs.pop('y_units','')
            y_type = kwargs.pop('y_type','linear')
            y_labels = kwargs.pop('y_labels',[])
            #label_size = kwargs.pop('label_size',0) # ignore 
            pdc = PairedDataContainer(pathname,shape, 
                                      y_data=y_data,
                                      x_data=x_data,
                                      x_units=x_units,
                                      x_type=x_type,
                                      y_units=y_units,
                                      y_type=y_type,
                                      y_labels = y_labels,
                                      )
            super().put_one_pd(pdc, col_index, (row_start, row_end))

        raise ValueError('Incompatible data for paired data can not be written to dss file')


    # @validate_call
    def preallocate_pd(
        self,
        pathname: Union[str, Path, PathLike,"DssPathName"],
        shape: Union[List[int],Tuple[int]],
        **kwargs: Any,
    ) -> None:
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return
        pdc = PairedDataContainer(pathname, shape, **kwargs)
        super().prealloc_pd(pdc)

    # @validate_call
    def read_grid(
        self, pathname: PathType, metadata_only: Optional[bool] = False
    ) -> SpatialGridStruct:
        """Reads both version 0 (DSS-6 format) and 100 (latest DSS-7 format) spatial grid data from dss file.

        Returns SpatialGridStruct object.
        """
        sg_st = SpatialGridStruct()
        retrieve_data = False if metadata_only else True
        # super().read_grid(pathname,sg_st,retrieve_data)
        grid_ver = self._get_gridver(pathname)

        if grid_ver is None:
            logging.error("Invalid grid data or version")
            return

        elif grid_ver == 100:
            logging.info("Reading modern format (DSS7) grid")
            super().read_grid100(pathname, sg_st, retrieve_data)

        else:
            logging.info(
                "Read grid version {} and convert it to version 100 grid".format(
                    grid_ver
                )
            )
            # find grid_type and create info6
            grid_type = self._get_gridtype(pathname)
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
            super().read_grid0(pathname, sg_st, info6, retrieve_data)

        return sg_st

    def read_grid2(
        self, pathname: PathType, metadata_only: Optional[bool] = False
    ) -> Optional[tuple]:
        """Reads both version 0 (DSS-6 format) and 100 (latest DSS-7 format) spatial grid data.

        Returns a tuple consisting of np.array and gridinfo.
        """
        retrieve_data = False if metadata_only else True
        grid_ver = self._get_gridver(pathname)
        if grid_ver is None:
            logging.error("Invalid grid data or version")
        elif grid_ver != 0:
            logging.info("Reading modern format (DSS7) grid")
            ds = self.read_grid(pathname, retrieve_data)
            if metadata_only:
                logging.info("Returning metadata of gridded data")
                return ds.gridinfo
            else:
                return ds.read(), ds.gridinfo
        else:
            logging.info("Reading older format (DSS6 or grid version 0) grid")
            # find grid_type and create info6
            grid_type = self._get_gridtype(pathname)
            info6 = GridInfo6.from_grid_type(grid_type)
            if grid_type == 430:
                # add space for crs defination, tz id generously
                # it should be more than what is in the file
                info6 = GridInfo6.get_specinfo6(50, 200, 50)
            # info6 is updated with data from the dss file
            data = super()._read_grid0_array(pathname, info6, retrieve_data)
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
        pathname: Optional[PathType] = None,
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
                pathname = data.pathname
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
                    raise Exception(
                        "For %s grid type, DPart and EPart of pathname must be datetime string"
                    )
                else:
                    # unsure about this param
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    stime = stime._toString(end_of_day=False)
                    etime = etime._toString(end_of_day=True)
                    pathobj.setDPart(stime)
                    pathobj.setEPart(etime)
                    pathname = pathobj.text()

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

        super().put_grid(pathname, _data, gridinfo)

    # @validate_call
    def put_grid0(
        self,
        data: Union["SpatialGridStruct", "np.array"],
        pathname: Optional[PathType] = None,
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
                pathname = data.pathname
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
                pathobj = DssPathName(pathname)
                dpart = pathobj.getDPart()
                epart = pathobj.getEPart()
                try:
                    stime = HecTime(dpart)
                    etime = HecTime(epart)
                except:
                    raise Exception(
                        "For %s grid type, DPart and EPart of pathname must be datetime string"
                    )
                else:
                    gridinfo.time_stamped = 1
                    # update D and E part of pathname
                    stime = stime._toString(end_of_day=False)
                    # 02JAN2025:0000 is changed to 01JAN2025:2400 with end_of_day = True
                    etime = etime._toString(end_of_day=True)
                    pathobj.setDPart(stime)
                    pathobj.setEPart(etime)
                    pathname = pathobj.text()

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

            gridinfo6 = gridinfo7_to_gridinfo6(gridinfo, pathname)

        if not _data.flags["C_CONTIGUOUS"]:
            _data = np.ascontiguousarray(_data)

        super().put_grid0(pathname, _data, gridinfo6)

    # @validate_call
    def copy(
        self,
        pathname_in: PathType,
        pathname_out: PathType,
        dss_out: Optional["Open"] = None,
    ) -> None:
        dss_fid = dss_out if isinstance(dss_out, self.__class__) else self
        if dss_fid.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if (
            pathname_in.lower() == pathname_out.lower() or not pathname_out
        ) and dss_fid is self:
            # overwriting with exact data is pointless
            return
        self.copyRecordsTo(dss_fid, pathname_in, pathname_out)

    # @validate_call
    def deletePathname(self, pathname: PathType) -> None:
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname = pathname.replace("//", "/*/")
        pathlist = self.getPathnameList(pathname)
        for pth in pathlist:
            status = deletePathname(self, pth)

    # @validate_call
    def getPathnameList(
        self, pathname: PathType, sort: Optional[bool] = False
    ) -> List[str]:
        # pathname string which can include wild card * for defining pattern
        catalog = getPathnameCatalog(self, pathname, sort)
        path_list = catalog.getPathnameList()
        return path_list

    # @validate_call
    def getPathnameDict(self) -> Dict[str, str]:
        # TODO: This does not work with DSS-6
        # This method necessary because type option in getPathnameList is not working
        path_dict = dict(
            zip(["TS", "RTS", "ITS", "PD", "GRID", "OTHER"], [[], [], [], [], [], []])
        )
        path_list = self.getPathnameList("")
        for path in path_list:
            path_dict[self._record_type(path)].append(path)
        return path_dict
