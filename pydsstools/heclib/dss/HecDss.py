"""
Open class object for HEC-DSS file

This module provides the public API for interacting with HEC-DSS files.
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
from ...core.enums import GridType
from ...core.gridinfo import GridInfo
from ...core.gridinfo.v6 import gridinfo7_to_gridinfo6, GridInfo6 
#from ...core.gridv6_internals import gridinfo7_to_gridinfo6, GridInfo6
from ...core import (
    PairedDataContainer,
    HecTime,
    DssPathName,
    UNDEFINED,
)

DateLike = TypeVar("DateLike", str, datetime, HecTime)
DateWindow: TypeAlias = Tuple[DateLike, DateLike]
PathType: TypeAlias = Union[str, Path, PathLike]



# ==================== Main Class ====================


class Open(_Open):
    """
    Open a DSS file and create a dataset object that supports input/output operations.

    This class provides a high-level, user-friendly interface for working with HEC-DSS
    files. It supports reading and writing time series, paired data, and spatial grid data.

    Parameters
    ----------
    dss_path : str or Path or PathLike
        Path to the DSS file.
    version : {6, 7} or None, optional
        DSS file version. If ``None``, detect automatically. If creating a new file,
        ``None`` creates a version 7 file. Default is None.
    mode : {"rw", "r"}, optional
        File open mode. ``"rw"`` allows read/write; ``"r"`` is read-only. Default is "rw".

    Attributes
    ----------
    mode : str
        The file access mode.
    version : int
        The DSS file version (6 or 7).
    filename : str
        Path to the DSS file.

    Examples
    --------
    Open a DSS file for reading and writing:

    >>> from pydsstools.heclib.dss.HecDss import Open
    >>> fid = Open("example.dss", mode="rw")

    Open a DSS file as read-only:

    >>> fid = Open("example.dss", mode="r")
    >>> fid.close()

    Use context manager for automatic cleanup:

    >>> with Open("example.dss") as fid:
    ...     ts = fid.read_ts("/A/B/C/01JAN2020/1HOUR/F/")

    See Also
    --------
    TimeSeriesContainer : Container for time series data
    PairedDataContainer : Container for paired data
    SpatialGridStruct : Structure for spatial grid data
    """

    def __init__(
        self,
        dss_path: PathType,
        version: Optional[Literal[6, 7]] = None,
        mode: Literal["rw", "r"] = "rw",
    ) -> None:
        super().__init__(dss_path, version)
        self.mode = mode

    def read_ts(
        self,
        pathname: Union[str, DssPathName],
        window: Optional[DateWindow] = None,
        trim_missing: bool = False,
        window_flag: Literal[0, 1, 2, 3] = 0,
        reg: Optional[bool] = False,
        ireg: Optional[bool] = False
    ) -> TimeSeriesStruct:
        """
        Read time-series record from DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        window : tuple of (start, end) or None, optional
            Time window to read. If ``None``, the date range encoded in the D-part of the
            ``pathname`` is used. Default is None.
        trim_missing : bool, optional
            If True, removes missing values at the beginning and end of the data set.
            Applies to regular time-series only. Default is False.
        window_flag : {0, 1, 2, 3}, optional
            Applies to irregular time series only. Controls how the time window
            is applied. Default is 0.

            Possible values:

            * 0 : Strictly adhere to the time window.
            * 1 : Also retrieve one value immediately before the start of the window.
            * 2 : Also retrieve one value immediately after the end of the window.
            * 3 : Retrieve one value immediately before the start and one immediately
              after the end of the window.
        reg : bool, optional
            If True, treat the data as a regular time series. Default is False.
        ireg : bool, optional
            If True, treat the data as an irregular time series. Default is False.

            If both ``reg`` and ``ireg`` are ``False`` or both are ``True``, the type of
            time series will be determined from the E-part of ``pathname``.

        Returns
        -------
        TimeSeriesStruct
            Time series data structure containing the requested data.

        Raises
        ------
        ValueError
            If pathname does not correspond to a valid time series record or if
            window_flag is invalid.

        Examples
        --------
        Read time series with a specific time window:

        >>> ts = fid.read_ts(pathname, window=('10MAR2006 24:00:00', '09APR2006 24:00:00'))

        Read entire time series:

        >>> ts = fid.read_ts(pathname)

        Read regular time series with trimming:

        >>> ts = fid.read_ts(pathname, trim_missing=True, reg=True)
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
                raise ValueError(
                    f"The pathname '{pathname.text()}' does not correspond to a valid "
                    f"regular or irregular time series record. Verify the E-part "
                    f"'{pathname.epart}' has a standard interval specification."
                )

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
            sdate = HecTime(start_date, midnight_as_2400=False)
            edate = HecTime(end_date, midnight_as_2400=True)
            sday = sdate.date()
            stime = sdate.time(2)
            eday = edate.date()
            etime = edate.time(2)
            return super()._read_ts_window(pathname.text(), sday, stime, eday, etime, retrieve_flag)

        else:
            retrieve_all = 0
            if (
                not pathname.dpart.strip()
            ):  # if date part is empty, retrieve all data ignoring date
                retrieve_all = 1
            return super()._read_ts_normal(
                pathname.text(), retrieve_flag, boolRetrieveAllTimes=retrieve_all
            )


    def put_ts(
        self, data: Union[str, "DssPathName", "TimeSeriesContainer"],
        **kwargs: Any
    ) -> None:
        """
        Write time-series data to DSS file.

        Parameters
        ----------
        data : str or DssPathName or TimeSeriesContainer
            Either a pathname string or a TimeSeriesContainer object.
        **kwargs : Any
            Keyword arguments for TimeSeriesContainer when ``data`` is a pathname.

            Required kwargs when data is pathname:

            * values : list or array-like
                Time series values.
            * For regular time-series (interval > 0):

                * start_time : str
                    Starting date/time.

            * For irregular time-series (interval < 0):

                * times : list of str
                    List of date/time strings.
                * julian_base : str, optional
                    Julian base date.

        Returns
        -------
        None

        Raises
        ------
        TypeError
            If data is not of expected type.
        ValueError
            If required parameters are missing or invalid.

        Examples
        --------
        Write using TimeSeriesContainer:

        >>> from pydsstools.heclib.dss.HecDss import Open
        >>> from pydsstools.core import TimeSeriesContainer
        >>> fid = Open("dss_file.dss", mode="rw")
        >>> pathname = r"/A/B/C//1HOUR/F/"
        >>> values = [10, 20, 30, 40, 50]
        >>> interval = 1
        >>> start_time = r"01JAN2025 1500"
        >>> data_units = "ft"
        >>> data_type = "inst"
        >>> timezone = "UTC"
        >>> tsc = TimeSeriesContainer(pathname, len(values), interval, values=values,
        ...                           start_time=start_time, data_units=data_units,
        ...                           data_type=data_type, tzid=timezone)
        >>> fid.put_ts(tsc)

        Write irregular time series without using TimeSeriesContainer:

        >>> pathname = r"/A/B/C//IR-DAY/F/"
        >>> julian_base = "01JAN2000"
        >>> times = ["02JUL2010 1200", "05JAN2012 0000", "15MAR2014 0200",
        ...          "25FEB2018 0500", "19DEC2024 1200"]
        >>> values = [1, 20, 30, 40, 50]
        >>> fid.put_ts(pathname, values=values, times=times, julian_base=julian_base,
        ...            data_units=data_units, data_type=data_type, tzid=timezone)
        """

        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if not isinstance(data, (str, DssPathName, TimeSeriesContainer)):
            raise TypeError(f"Expected pathname or TimeSeriesContainer, got {type(data).__name__}.")

        if isinstance(data, TimeSeriesContainer):
            tsc = data
            if tsc.interval > 0:
                # Regular time-series
                if not tsc.start_time:
                    raise ValueError("Start date/time for regular timeseries container is not provided")

            else:
                # Irregular time-series
                if tsc.times is None:
                    raise ValueError("Times for irregular timeseries container is not provided")

            if tsc.values is None:
                raise ValueError("Values for timeseries container is not provided")

        else:
            pathname = DssPathName(data)
            if "pathname" in kwargs:
                logging.warning("Ignoring pathname for TimeSeriesContainer provided as keyword argument")

            # -1 = irregular
            #  1 = regular
            #  0 = invalid
            interval = self._ts_type_from_pathname(pathname.text())
            if interval == 0:
                raise ValueError("The pathname for timeseries has invalid interval information")

            values = kwargs["values"]
            count = len(values)
            _count = kwargs.pop("count", None)

            if _count is not None:  # noqa: SIM102
                if _count != count:
                    logging.warning(f"Ignoring count argument value (={_count}) as it is not equal to the length of values (={count})")

            if interval < 0:
                # required for irregular time-series
                times = kwargs["times"]

            tsc = TimeSeriesContainer(pathname.text(), count, interval, **kwargs)

        super()._put(tsc)

    def read_pd(
        self,
        pathname: Union[str, "DssPathName"],
        window: Optional[Tuple[int, int, int, int]] = None,
        dataframe: Optional[bool] = True,
    ) -> Union[pd.DataFrame, PairedDataStruct]:
        """
        Read paired data from DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        window : tuple of (int, int, int, int) or None, optional
            Index window to read. If ``None``, all rows and columns are read.
            Default is None.

            Supported forms:

            * ``(row_start, row_end, col_start, col_end)``

            Indexing rules:

            * Zero-based and **inclusive at both ends**.
            * ``row_start`` / ``col_start`` >= 0 (first row/column is 0).
            * ``row_end`` / ``col_end`` <= last valid index.
            * ``None`` for any bound selects the respective first/last index.
            * Negative indices are allowed (Python-style) and are **wrapped**.
            * If an **end** index overflows the table size, it is **clipped**.
            * Any other out-of-range condition raises ``IndexError``.
        dataframe : bool, optional
            If True, return a pandas DataFrame. If False, return a PairedDataStruct
            object. Default is True.

        Returns
        -------
        pandas.DataFrame or PairedDataStruct
            Paired data in the requested format.

        Raises
        ------
        IndexError
            If window indices are invalid or out of range.

        Examples
        --------
        Read paired data with a window:

        >>> df = fid.read_pd(pathname, window=(2, 5, 0, None))

        Read all paired data:

        >>> df = fid.read_pd(pathname)

        Read as PairedDataStruct:

        >>> pds = fid.read_pd(pathname, dataframe=False)
        """
        pathname = DssPathName(pathname)

        if window:
            logging.debug(f"Input paired data window = '{window}'")
            size_info = self._pd_info(pathname.text())
            rows = size_info["data_no"]
            cols = size_info["curve_no"]
            # user's 0-based indices
            _row_start, _row_end, _col_start, _col_end = window

            row_start, row_end = _normalize_span(rows, _row_start, _row_end)
            col_start, col_end = _normalize_span(cols, _col_start, _col_end)

            window = (row_start, row_end, col_start, col_end)

            # updated zero based indices
            _row_start, _row_end, _col_start, _col_end = [x - 1 for x in window]

            logging.debug(f"Updated window = '{window}'")

        pds = super()._read_pd(pathname.text(), window)

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
                _col_end = tb.shape[1] - 1

            primary_colnames = [f"y{i}" for i in range(_col_start, _col_end + 1)]
            alias_colnames = ['' for x in range(_col_start, _col_end + 1)]

            logging.debug(f'window:{window}')
            logging.debug(f'col_start/end: {_col_start},{_col_end}')
            logging.debug(f'primary colnames: {primary_colnames}')
            logging.debug(f'alias columns: {alias_colnames}')

            for i, label in enumerate(y_labels):
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

    def read_pd_labels(self, pathname: Union[str, "DssPathName"]) -> Dict[str, str]:
        """
        Read paired data labels from DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.

        Returns
        -------
        dict of str to str
            Dictionary mapping primary column names to label names.

        Examples
        --------
        >>> labels = fid.read_pd_labels("/A/B/STAGE-FLOW/D/E/F/")
        >>> print(labels)
        {'y0': 'Stage', 'y1': 'Flow'}
        """
        pathname = DssPathName(pathname)
        _df = self.read_pd(pathname.text(), window=(0, 0, 0, None))
        label0 = _df.columns.get_level_values(0).tolist()
        label1 = _df.columns.get_level_values(1).tolist()
        return dict(zip(label0, label1))

    def pd_info(self, pathname: Union[str, "DssPathName"]) -> Dict[str, Any]:
        """
        Get information about a paired data record.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.

        Returns
        -------
        dict
            Dictionary containing paired data information with keys:

            - 'curve_no' : int
                Number of curves (columns).
            - 'data_no' : int
                Number of data points (rows).
            - 'dtype' : int
                Data type code.
            - 'label_size' : int
                Average label size in characters.

        Examples
        --------
        >>> info = fid.pd_info("/A/B/STAGE-FLOW/D/E/F/")
        >>> print(f"Curves: {info['curve_no']}, Points: {info['data_no']}")
        Curves: 2, Points: 100
        """
        pathname = DssPathName(pathname)
        return super()._pd_info(pathname.text())

    def put_pd(
        self,
        data: Union["PairedDataContainer", str, "DssPathName"],
        **kwargs: Any,
    ) -> None:
        """
        Write new paired data or edit an existing paired data record in the DSS file.

        Parameters
        ----------
        data : PairedDataContainer or str or DssPathName
            Input data to write. Can be:

            * A PairedDataContainer object.
            * A string or DssPathName specifying an existing or new DSS record pathname.

        **kwargs : Any
            Additional keyword arguments or attributes for the PairedDataContainer.

            When writing a DataFrame:

            * y_data : pandas.DataFrame
                DataFrame containing paired data.
            * x_units : str
                Units for x-axis data.
            * x_type : str
                Type of x-axis data (e.g., "linear").
            * y_units : str
                Units for y-axis data.
            * y_type : str
                Type of y-axis data (e.g., "linear").

            When writing a single curve to preallocated record:

            * col_index : int
                Column index (0-based) to write to.
            * y_data : list or array-like
                Y-axis values for the curve.
            * window : tuple of (int, int), optional
                Row range (start, end) for writing.
            * y_labels : list of str, optional
                Labels for y-axis curves.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If incompatible parameters are provided or indices are out of range.
        IndexError
            If data has too many values.

        Examples
        --------
        Write PairedDataContainer:

        >>> from pydsstools.core import PairedDataContainer
        >>> pathname = "/A/B/STAGE-FLOW/D/E/F/"
        >>> curves = 2
        >>> rows = 5
        >>> pdc = PairedDataContainer(pathname, (rows, curves))
        >>> pdc.x_data = [0.1, 0.2, 0.3, 0.4, 0.5]
        >>> pdc.y_data = [[10, 20, 30, 40, 50], [1, 2, 3, 4, 5]]
        >>> pdc.x_units = "ft"
        >>> pdc.x_type = "linear"
        >>> pdc.y_units = "cfs"
        >>> pdc.y_type = "linear"
        >>> fid.put_pd(pdc)

        Write DataFrame:

        >>> import pandas as pd
        >>> pathname = "/A/B/STAGE-FLOW/D/E/F/"
        >>> df = pd.DataFrame({"Curve #1": [1, 2], "Curve #2": [3, 4]}, index=[0.5, 0.6])
        >>> fid.put_pd(pathname, x_units="ft", x_type="linear", y_data=df,
        ...            y_units="cfs", y_type="linear")

        Write a curve to preallocated paired data record:

        >>> pathname = "/A/B/STAGE-FLOW/D/E/PREALLOC/"
        >>> fid.put_pd(pathname, col_index=2, y_data=[1, 2, 3, 4], window=(2, 5))
        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if isinstance(data, PairedDataContainer):
            super()._put_pd(data)
            return

        if isinstance(data, (str, DssPathName)):
            pathname = DssPathName(data)
            y_data = kwargs.pop("y_data", None)
            col_index = kwargs.pop("col_index", None)

            if "pathname" in kwargs:
                logging.warning("Ignoring pathname for PairedDataContainer provided as keyword argument")

            if isinstance(y_data, pd.DataFrame):
                logging.info('Writing paired data from DataFrame')
                df = y_data
                shape = df.shape

                pdc = PairedDataContainer(pathname.text(), shape, **kwargs)
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
                super()._put_pd(pdc)
                return

            elif isinstance(col_index, int):
                logging.info('Writing single paired data curve to preallocated paired data set')
                # pd_info raise error if the record does not exist
                size_info = self._pd_info(pathname.text())
                rows = size_info["data_no"]
                cols = size_info["curve_no"]
                logging.debug(f"The paired data record ({pathname.text()}) in file has rows={rows} and cols={cols}")

                # 1-based col_index
                logging.debug(f"Input 0-based col_index = {col_index}")
                col_index, _ = _normalize_span(cols, col_index, None)
                logging.debug(f"Updated 1-based col_index = {col_index}")

                # 1-based default indices
                row_start, row_end = (1, rows)
                logging.debug(f"1-based (row_start,row_end) assuming full curve data is replaced: ({row_start},{row_end}).")

                # update indices based on input
                window = kwargs.pop("window", None)
                if window:
                    if not isinstance(window, (tuple, list)):
                        raise ValueError("The window for writing single paired data must be tuple/list containing start and end row indices.")

                    if len(window) < 2:
                        raise ValueError(f"The window for writing single paired data curve must contain two integers; provided '{window}'.")

                    elif len(window) > 2:
                        window = window[0:2]

                    # 0-based
                    _row_start, _row_end = window
                    logging.debug(f"0-based (row_start,row_end) provided as input: ({_row_start},{_row_end}).")
                    # 1-based
                    row_start, row_end = _normalize_span(rows, _row_start, _row_end)
                    logging.debug(f"1-based (row_start,row_end) derived from input: ({row_start},{row_end}).")

                y_labels = kwargs.pop('y_labels', [])

                # Verify y_data has ndim == 1, or if ndim == 2 shape[0] == 1
                _y_data = y_data
                if isinstance(y_data, (tuple, list)):
                    _y_data = np.array(y_data, np.float32)

                if not isinstance(_y_data, np.ndarray):
                    raise TypeError("y_data for paired data is not of valid type")

                if _y_data.ndim > 2:
                    raise ValueError("The dimension of y_data should be 1 or 2.")

                if _y_data.ndim == 1:
                    _y_data = np.ascontiguousarray(_y_data.reshape(1, -1))

                if _y_data.ndim == 2 and _y_data.shape[0] != 1:
                    logging.warning("The y_data for single curve has multiple rows; flattening the data as single row of values.")
                    _y_data = np.ascontiguousarray(_y_data.reshape(1, -1))

                y_data = _y_data

                shape = (y_data.shape[1], 1)

                if shape[0] + row_start - 1 > rows:
                    raise IndexError("y_data has too many values exceeding allowable row_end index")

                # update  row_end based on number of y_data values
                if row_end != row_start + shape[0] - 1:
                    logging.debug("row_end updated based on the number of y_data")
                    row_end = row_start + shape[0] - 1

                logging.debug(f"Single paired data curve to be written with 1-based row_start={row_start} and row_end={row_end}. Total rows in dss = {rows}.")
                pdc = PairedDataContainer(pathname.text(), shape,
                                        y_data=y_data,
                                        x_data=None,
                                        x_units=None,
                                        x_type=None,
                                        y_units=None,
                                        y_type=None,
                                        y_labels=y_labels,
                                        )

                super()._put_one_pd(pdc, col_index, (row_start, row_end))
                return

        raise ValueError('Incompatible input parameters provided to write paired data to dss file')


    def preallocate_pd(
        self,
        pathname: Union[str, "DssPathName"],
        shape: Union[List[int], Tuple[int, int]],
        **kwargs: Any,
    ) -> None:
        """
        Preallocate space for paired data record in DSS file.

        This method creates an empty paired data structure in the DSS file that can
        later be filled with individual curves using put_pd with col_index parameter.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        shape : list of int or tuple of (int, int)
            Shape of the paired data as (rows, columns).
        **kwargs : Any
            Additional keyword arguments for PairedDataContainer initialization, such as
            x_units, y_units, x_type, y_type, etc.

        Returns
        -------
        None

        Examples
        --------
        >>> pathname = "/A/B/STAGE-FLOW/D/E/PREALLOC/"
        >>> fid.preallocate_pd(pathname, shape=(100, 5), x_units="ft", y_units="cfs")
        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname = DssPathName(pathname)
        pdc = PairedDataContainer(pathname.text(), shape, **kwargs)
        super()._prealloc_pd(pdc)

    def read_grid(
        self, pathname: Union[str, "DssPathName"], metadata_only: Optional[bool] = False
    ) -> SpatialGridStruct:
        """
        Read spatial grid data from DSS file.

        Reads both version 0 (DSS-6 format) and version 100 (latest DSS-7 format) spatial
        grid data from DSS file. The method automatically detects the grid version and
        converts older formats to the modern format.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        metadata_only : bool, optional
            If True, read only metadata without grid data. Default is False.

        Returns
        -------
        SpatialGridStruct
            Spatial grid data structure containing grid data and metadata.

        Examples
        --------
        Read grid data:

        >>> sg = fid.read_grid("/A/B/PRECIP/01JAN2020:0000/01JAN2020:2400/GRIDTYPE/")

        Read only metadata:

        >>> sg = fid.read_grid(pathname, metadata_only=True)
        >>> print(sg.gridinfo.shape)
        (100, 200)

        Notes
        -----
        .. todo::
           Support reading version-0 grids stored in DSS-7 files.
        """
        pathname = DssPathName(pathname)
        sg_st = SpatialGridStruct()
        retrieve_data = False if metadata_only else True
        grid_ver = self._get_gridver(pathname.text())

        if grid_ver is None:
            logging.error("Invalid grid data or version")
            return

        elif grid_ver == 100:
            logging.info("Reading modern format (DSS7) grid")
            super()._read_grid100(pathname.text(), sg_st, retrieve_data)

        else:
            logging.info(
                "Read grid version {} and convert it to version 100 grid".format(
                    grid_ver
                )
            )

            #if self.version == 7:
            #    raise NotImplementedError("Reading version {} from from DSS7 file is not implemented.", grid_ver)

            # find grid_type and create gridinfo6
            grid_type = self._get_gridtype(pathname.text())
            logging.debug("grid type is {}".format(grid_type))
            gridinfo6 = GridInfo6.from_grid_type(grid_type)
            logging.debug("grid type in gridinfo6 is {}".format(gridinfo6.grid_type))
            if grid_type == 430:
                # add space for crs definition, tz id generously
                # it should be more than what is in the file
                gridinfo6 = GridInfo6.get_specinfo6(50, 200, 50)
                logging.debug(
                    "grid type in updated gridinfo6 is {}".format(gridinfo6.grid_type)
                )
            super()._read_grid0(pathname.text(), sg_st, gridinfo6, retrieve_data)

        return sg_st

    def read_grid2(
        self, pathname: Union[str, "DssPathName"], metadata_only: Optional[bool] = False
    ) -> Optional[Union[Tuple[np.ndarray, GridInfo], GridInfo]]:
        """
        Read spatial grid data from DSS file and return as tuple.

        Reads both version 0 (DSS-6 format) and version 100 (latest DSS-7 format) spatial
        grid data. This method provides an alternative return format compared to read_grid.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        metadata_only : bool, optional
            If True, return only metadata (gridinfo). Default is False.

        Returns
        -------
        tuple of (numpy.ndarray, GridInfo) or GridInfo or None
            If metadata_only is False, returns tuple of (numpy.ndarray, gridinfo).
            If metadata_only is True, returns gridinfo only.
            Returns None if grid data is invalid.

        Examples
        --------
        Read grid as array and gridinfo:

        >>> data, gridinfo = fid.read_grid2(pathname)
        >>> print(data.shape, gridinfo.grid_type)

        Read only gridinfo:

        >>> gridinfo = fid.read_grid2(pathname, metadata_only=True)
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

            #if self.version == 7:
            #    raise NotImplementedError("Reading version {} from from DSS7 file is not implemented.", grid_ver)

            # find grid_type and create gridinfo6
            grid_type = self._get_gridtype(pathname.text())
            gridinfo6 = GridInfo6.from_grid_type(grid_type)
            if grid_type == 430:
                # TODO: Investigate why locally run pytest randomly corrupts the spec type grid data
                # add space for crs definition, tz id generously
                # it should be more than what is in the file
                gridinfo6 = GridInfo6.get_specinfo6(50, 200, 50)
            # gridinfo6 is updated with data from the dss file
            data = super()._read_grid0_array(pathname.text(), gridinfo6, retrieve_data)
            if metadata_only:
                logging.info("Returning metadata of gridded data")
                if data is not None:
                    return gridinfo6
            if data is not None:
                logging.info("Returning metadata/data of gridded data")
                return data, gridinfo6

    def put_grid(
        self,
        data: Union["SpatialGridStruct", np.ndarray],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[GridInfo] = None,
        flipud: Optional[bool] = True,
        inplace: Optional[bool] = False,
        compute_stats: Optional[Union[bool, List[float]]] = True,
        transform: Optional[Any] = None,
        normalize: Optional[bool] = True,
    ) -> None:
        """
        Write spatial grid to DSS-7 file.

        Writing to DSS-6 file is not allowed. Use put_grid0 for DSS-6 files.

        Parameters
        ----------
        data : SpatialGridStruct or numpy.ndarray or numpy.ma.MaskedArray
            Grid data to write.

            * **numpy.ndarray**: ``np.nan`` and ``nodata`` (from ``gridinfo``)
               and ``UNDEFINED`` values are treated as nodata.
            * **numpy.ma.MaskedArray**: masked elements are treated as nodata.
            * **SpatialGridStruct**: a structured object containing grid and metadata.
        pathname : str or DssPathName or None, optional
            Pathname for the DSS record. It can be None for SpatialGridStruct. The dates
            in parts D and E are automatically reformatted to correct convention. Part D
            uses the beginning of the day (e.g., ``02JAN2025:0000``) while Part E uses
            the end of the previous day convention (e.g., ``01JAN2025:2400``).
            Default is None.
        gridinfo : GridInfo or subclass or None, optional
            Metadata describing the grid. Can be one of:

            * ``GridInfo``, ``HrapInfo``, or ``AlbersInfo``: requires ``data_type``,
              ``cell_size``, ``shape`` at minimum.
            * ``SpecifiedInfo``: additionally ``nodata`` and ``crs``.

            Default is None.
        flipud : bool, optional
            If True, flips the rows of the data array upside down before writing.
            This is necessary when the input data is numpy array with origin at top-left
            (e.g., array representing raster image in rasterio).  Default is True.
        inplace : bool, optional
            If True, tries to modify the data in place to reduce memory usage. Default is False.
        compute_stats : bool or list of float, optional
            Controls whether and how statistics are computed for the grid data.
            Default is True.

            Possible values:

            * **True**: compute min, max, mean, range values, and range counts.
            * **False**: do not compute statistics.
            * **list of float**: compute "greater than or equal to" counts for the
              specified values (maximum of 19 thresholds, excluding nodata).
        transform : Any or None, optional
            Spatial transform information (e.g., affine transform). If provided, it
            overrides transform parameters in ``gridinfo``. Default is None.
        normalize : bool, optional
            If True, tries to normalize coords_cell0 and lower_left_cell based on min_xy or input transform parameter. Default is True.

        Returns
        -------
        None

        Raises
        ------
        Exception
            If D-part or E-part is not a valid datetime string for time-stamped grids.

        Examples
        --------
        Write grid from array:

        >>> import numpy as np
        >>> from pydsstools.core.gridinfo import SpecifiedGridInfo
        >>> data = np.random.rand(100, 200).astype(np.float32)
        >>> pathname = "/A/B/PRECIP/01JAN2020:0000/01JAN2020:2400/SHG/"
        >>> gridinfo = SpecifiedGridInfo(data_type="PER-CUM", cell_size=2000.0,
        ...                              lower_left_x=100000, lower_left_y=200000,
        ...                              rows=100, cols=200, nodata=-999.0)
        >>> fid.put_grid(data, pathname, gridinfo)

        Write with custom statistics thresholds:

        >>> fid.put_grid(data, pathname, gridinfo, compute_stats=[0, 10, 50, 100])
        """

        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 6:
            logging.warning("Writing DSS grid record in DSS-6 file is not supported")
            return
        
        if not isinstance(data, (SpatialGridStruct, np.ndarray)):
            raise TypeError(f"Expected SpatialGridStruct or numpy.ndarray, got {type(data).__name__}.")

        if isinstance(data, SpatialGridStruct):
            # use this for copying from one file to another or updating statistics
            if pathname is None:
                pathname = DssPathName(data.pathname)
            else:
                pathname = DssPathName(pathname)

            gridinfo = data.gridinfo

        elif isinstance(data, np.ndarray):
            if not isinstance(gridinfo, GridInfo):
                logging.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logging.error(
                    "Provide valid pathname for grid record!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)

        # Verify pathname has valid datetime stamps when grid is specified to have time component
        if gridinfo.grid_type_has_time():
            dpart = pathname.dpart
            epart = pathname.epart
            try:
                # check if dpart, epart or both are not datetime
                # TODO: Found out HecTime('1') passes this test
                stime = HecTime(dpart, midnight_as_2400=False, date_style=2, time_style=0)
                etime = HecTime(epart, midnight_as_2400=True, date_style=2, time_style=0)
            except:
                raise Exception(
                    "For %s grid type, DPart and EPart of pathname must be datetime string"
                )
            else:
                # unsure about this param
                gridinfo.time_stamped = 1
                # update D and E part of pathname
                pathname.dpart = stime.text()
                pathname.epart = etime.text()

        grid_type = gridinfo.grid_type
        shape = gridinfo.shape
        nodata = UNDEFINED

        if grid_type == GridType.specified or grid_type == GridType.specified_time:
            nodata = gridinfo.nodata
        
        _data,stats = _sanitize_grid_array_for_dss_write(data,nodata,shape,flipud,inplace,compute_stats)

        if stats:
            gridinfo.max_val = stats["max_val"]
            gridinfo.min_val = stats["min_val"]
            gridinfo.mean_val = stats["mean_val"]
            gridinfo.range_vals = stats["range_vals"]
            gridinfo.range_counts = stats["range_counts"]

        if normalize:
            gridinfo.normalize(transform)

        super()._put_grid(pathname.text(), _data, gridinfo)

    def put_grid0(
        self,
        data: Union["SpatialGridStruct", np.ndarray],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[Union[GridInfo, GridInfo6]] = None,
        flipud: Optional[bool] = True,
        inplace: Optional[bool] = False,
        compute_stats: Optional[Union[bool, List[float]]] = True,
        transform: Optional[Any] = None,
        normalize: Optional[bool] = True,
    ) -> None:
        """
        Write spatial grid to DSS-6 file.

        Writing to DSS-7 file using this method is experimental and may cause problems.
        Use put_grid for DSS-7 files instead.

        Parameters
        ----------
        data : SpatialGridStruct or numpy.ndarray or numpy.ma.MaskedArray
            Grid data to write.

            * **numpy.ndarray**: ``np.nan`` and ``nodata`` (from ``gridinfo``)
               and ``UNDEFINED`` values are treated as nodata.
            * **numpy.ma.MaskedArray**: masked elements are treated as nodata.
            * **SpatialGridStruct**: a structured object containing grid and metadata.
        pathname : str or DssPathName or None, optional
            Pathname for the DSS record. It can be None for SpatialGridStruct. The dates
            in parts D and E are automatically reformatted to correct convention. Part D
            uses the beginning of the day (e.g., ``02JAN2025:0000``) while Part E uses
            the end of the previous day convention (e.g., ``01JAN2025:2400``).
            Default is None.
        gridinfo : GridInfo or GridInfo6 or None, optional
            Metadata describing the grid for version 6 and 7. Default is None.
        flipud : bool, optional
            If True, flips the rows of the data array upside down before writing.
            This is necessary when the input data is numpy array with origin at top-left
            (e.g., array representing raster image in rasterio).  Default is True.
        inplace : bool, optional
            If True, tries to modify the data in place to reduce memory usage. Default is False.
        compute_stats : bool or list of float, optional
            Controls whether and how statistics are computed for the grid data.
            Default is True.

            Possible values:

            * **True**: compute min, max, mean, range values, and range counts.
            * **False**: do not compute statistics.
            * **list of float**: compute "greater than or equal to" counts for the
              specified values (maximum of 19 thresholds, excluding nodata).
        transform : Any or None, optional
            Spatial transform information (e.g., affine transform). If provided, it
            overrides transform parameters in ``gridinfo``. Default is None.
        normalize : bool, optional
            If True, tries to normalize coords_cell0 and lower_left_cell based on min_xy or input transform parameter. Default is True.

        Returns
        -------
        None

        Raises
        ------
        Exception
            If D-part or E-part is not a valid datetime string for time-stamped grids.

        Notes
        -----
        This method writes grid data in DSS-6 (version 0) format. It is primarily
        intended for maintaining compatibility with legacy DSS-6 files.
        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 7:
            logging.warning(
                "Writing version 0 (DSS-6 format) grid data to DSS7 file is experimental."
            )

        if not isinstance(data, (SpatialGridStruct, np.ndarray)):
            raise TypeError(f"Expected SpatialGridStruct or numpy.ndarray, got {type(data).__name__}.")

        if isinstance(data, SpatialGridStruct):
            # use this for copying from one file to another or updating statistics
            if pathname is None:
                pathname = DssPathName(data.pathname)
            else:
                pathname = DssPathName(pathname)

            gridinfo = data.gridinfo

        elif isinstance(data, np.ndarray):
            if not isinstance(gridinfo, GridInfo):
                logging.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logging.error(
                    "Provide valid pathname for grid record!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)

            # convert to gridinfo from verion 0 or 6 to 7, which is easier to work with
            if isinstance(gridinfo, GridInfo6):
                gridinfo = gridinfo.to_gridinfo7()

        # Verify pathname has valid datetime stamps when grid is specified to have time component
        if gridinfo.grid_type_has_time():
            dpart = pathname.dpart
            epart = pathname.epart
            try:
                # check if dpart, epart or both are not datetime
                # TODO: Found out HecTime('1') passes this test
                stime = HecTime(dpart, midnight_as_2400=False, date_style=4, time_style=0)
                etime = HecTime(epart, midnight_as_2400=True, date_style=4, time_style=0)
            except:
                raise Exception(
                    "For %s grid type, DPart and EPart of pathname must be datetime string"
                )
            else:
                # unsure about this param
                gridinfo.time_stamped = 1
                # update D and E part of pathname
                pathname.dpart = stime.text()
                pathname.epart = etime.text()

        grid_type = gridinfo.grid_type
        shape = gridinfo.shape
        nodata = UNDEFINED

        if grid_type == GridType.specified or grid_type == GridType.specified_time:
            nodata = gridinfo.nodata
        
        _data,stats = _sanitize_grid_array_for_dss_write(data,nodata,shape,flipud,inplace,compute_stats)

        if stats:
            gridinfo.max_val = stats["max_val"]
            gridinfo.min_val = stats["min_val"]
            gridinfo.mean_val = stats["mean_val"]
            gridinfo.range_vals = stats["range_vals"]
            gridinfo.range_counts = stats["range_counts"]

        if normalize:
            gridinfo.normalize(transform)

        gridinfo6 = gridinfo7_to_gridinfo6(gridinfo, pathname.text())

        super()._put_grid0(pathname.text(), _data, gridinfo6)

    def copy_path(
        self,
        pathname_in: Union[str, "DssPathName"],
        pathname_out: Union[str, "DssPathName"],
        dss_out: Optional["Open"] = None,
    ) -> None:
        """
        Copy a DSS record from one pathname to another.

        Can copy within the same file or to a different DSS file.

        Parameters
        ----------
        pathname_in : str or DssPathName
            Source pathname to copy from.
        pathname_out : str or DssPathName
            Destination pathname to copy to.
        dss_out : Open or None, optional
            Destination DSS file object. If None, copies within the same file.
            Default is None.

        Returns
        -------
        None

        Examples
        --------
        Copy within same file:

        >>> fid.copy_path("/A/B/C/D/E/F/", "/A/B/C_COPY/D/E/F/")

        Copy to different file:

        >>> with Open("target.dss", mode="rw") as fid_out:
        ...     fid.copy_path("/A/B/C/D/E/F/", "/A/B/C/D/E/F/", dss_out=fid_out)
        """
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
        self._copyRecordsTo(dss_fid, pathname_in.text(), pathname_out.text())

    def del_path(self, pathname: Union[str, "DssPathName"]) -> None:
        """
        Delete DSS record(s) matching the given pathname pattern.

        Parameters
        ----------
        pathname : str or DssPathName
            Pathname or pathname pattern to delete. Supports wildcards (*).

        Returns
        -------
        None

        Examples
        --------
        Delete specific record:

        >>> fid.del_path("/A/B/C/D/E/F/")

        Delete multiple records with wildcards:

        >>> fid.del_path("/A/B/*/D/E/F/")
        """
        if self.mode != "rw":
            logging.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname_pattern = _process_pathname_pattern(pathname)
        pathlist = self.getPathnameList(pathname_pattern)
        for pth in pathlist:
            status = self._delete_pathname(pth)

    def search_path(
        self, pathname: Union[str, "DssPathName"] = "", sort: Optional[bool] = False
    ) -> List[str]:
        """
        Search for DSS pathnames matching a pattern.

        Parameters
        ----------
        pathname : str or DssPathName, optional
            Pathname pattern which can include wildcard (*) for defining search pattern.
            Empty string returns all pathnames. Default is "".
        sort : bool, optional
            If True, sort the returned pathnames. Default is False.

        Returns
        -------
        list of str
            List of matching pathnames.

        Examples
        --------
        Get all pathnames:

        >>> paths = fid.search_path()

        Search with pattern:

        >>> paths = fid.search_path("/A/B/*/D/E/F/")

        Get sorted results:

        >>> paths = fid.search_path("/A/*/*/*/*/F/", sort=True)
        """
        if pathname:
            pathname = _process_pathname_pattern(pathname)

        catalog = self._get_catalog(pathname, sort)
        path_list = catalog.paths()
        return path_list

    def path_dict(self, sub_type: Optional[bool] = False) -> Dict[str, List[str]]:
        """
        Get all pathnames in DSS file organized by data type.

        Parameters
        ----------
        sub_type : bool, optional
            If True, separate time series into regular and irregular, and grids by type.
            If False, group all time series together and all grids together.
            Default is False.

        Returns
        -------
        dict of str to list of str
            Dictionary mapping data type names to lists of pathnames.

            When sub_type is True, keys include:

            * "ts-reg": Regular time series
            * "ts-irreg": Irregular time series
            * "pd": Paired data
            * "text": Text data
            * "text-table": Text tables
            * "grid-undefined": Undefined grid type
            * "grid-hrap": HRAP grids
            * "grid-albers": Albers grids
            * "grid-spec": Specified grids
            * "tin": TIN data
            * "location": Location data
            * "array": Array data
            * "image": Image data
            * "generic": Generic data
            * "undefined": Undefined data types

            When sub_type is False, keys include:

            * "ts": All time series (regular + irregular)
            * "grid": All grids (undefined + hrap + albers + specified)
            * Other keys same as above

        Examples
        --------
        Get all paths grouped by general type:

        >>> paths = fid.path_dict()
        >>> print(f"Time series: {len(paths['ts'])}")
        >>> print(f"Paired data: {len(paths['pd'])}")

        Get paths with detailed sub-types:

        >>> paths = fid.path_dict(sub_type=True)
        >>> print(f"Regular TS: {len(paths['ts-reg'])}")
        >>> print(f"Irregular TS: {len(paths['ts-irreg'])}")
        """
        ts_rts = []
        ts_its = []
        pd = []
        text_data = []
        text_table = []
        grid_undefined = []
        grid_hrap = []
        grid_albers = []
        grid_spec = []
        tin = []
        location = []
        array_data = []
        image_data = []
        generic_data = []
        undefined_data = []

        path_list = self.search_path("")
        for path in path_list:
            name = self._record_type_name(path, abbr=True)
            logging.debug(f"{path} is record type {name}.")
            name = name.upper()
            if name.startswith("RT"):
                ts_rts.append(path)
            elif name.startswith("IT"):
                ts_its.append(path)
            elif name.startswith("PD"):
                pd.append(path)
            elif name.startswith("TXT"):
                text_data.append(path)
            elif name.startswith("TT"):
                text_table.append(path)
            elif name.startswith("UG"):
                grid_undefined.append(path)
            elif name.startswith("HG"):
                grid_hrap.append(path)
            elif name.startswith("AG"):
                grid_albers.append(path)
            elif name.startswith("SG"):
                grid_spec.append(path)
            elif name.startswith("SPA"):
                tin.append(path)
            elif name.startswith("LOC"):
                location.append(path)
            elif name.startswith("ARR"):
                array_data.append(path)
            elif name.startswith("IM"):
                image_data.append(path)
            elif name.startswith("GEN"):
                generic_data.append(path)
            else:
                undefined_data.append(path)

        if sub_type:
            result = {
                "ts-reg": ts_rts,
                "ts-irreg": ts_its,
                "pd": pd,
                "text": text_data,
                "text-table": text_table,
                "grid-undefined": grid_undefined,
                "grid-hrap": grid_hrap,
                "grid-albers": grid_albers,
                "grid-spec": grid_spec,
                "tin": tin,
                "location": location,
                "array": array_data,
                "image": image_data,
                "generic": generic_data,
                "undefined": undefined_data,
            }
        else:
            result = {
                "ts": ts_rts + ts_its,
                "pd": pd,
                "text": text_data,
                "text-table": text_table,
                "grid": grid_undefined + grid_hrap + grid_albers + grid_spec,
                "tin": tin,
                "location": location,
                "array": array_data,
                "image": image_data,
                "generic": generic_data,
                "undefined": undefined_data,
            }

        return result


# ==================== Helper Functions ====================


def _normalize_span(
    size: int,
    start0: Optional[int],
    end0: Optional[int],
) -> Tuple[int, int]:
    """
    Convert 0-based indices to 1-based indices for paired data.

    Python functions expect 0-based indices while C API uses 1-based indices.

    Parameters
    ----------
    start0 : int or None
        Start index (0-based). If None, defaults to 0.
    end0 : int or None
        End index (0-based). If None, defaults to size-1.
    size : int
        Total size of the span being indexed.

    Returns
    -------
    tuple of (int, int)
        Tuple containing (start, end) as 1-based indices.

    Raises
    ------
    IndexError
        If indices are out of range or invalid.
    """
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


def _sanitize_grid_array_for_dss_write(data,nodata,shape,flipud=True,inplace=False,compute_stats=False,range_values=None):
    # UNDEFINED is treated as nodata for gridded data. Additional nodata value is associated with Specified Grid.
    # TODO: masked elements and nans are converted to nodata; is it better to use UNDEFINED instead?

    is_masked = isinstance(data,ma.core.MaskedArray)
    is_sgrid = isinstance(data,SpatialGridStruct)
    is_nodata_undefined = nodata == UNDEFINED

    # Convert data to _data and mask arrays
    mask = None
    _data = data

    is_copied = False
    make_copy = not inplace

    if is_masked:
        # data is masked array
        _data = data._data
        mask = data.mask

        if _data.dtype != np.float32:
            # float32 and c_contiguous
            _data = _data.astype(np.float32, order="C", casting="unsafe", copy=True)
            _data[mask] = nodata
            is_copied = True

        elif not make_copy:
            # replace masked elements with nodata (ignoring array's fill value that can be arbitrary value)
            # TODO: check if setting fill value has any side effect in some cases
            data.set_fill_value(nodata)
            data.data[mask] = nodata

        else:
            _data = data.filled(nodata)

    elif is_sgrid:
        _data = data._get_mview()
        _data.setflags(write=1)
        # memory view is (rows*cols,) 1D array
        # reshape it to raster 2d-array without copy
        # buffer is laid out consistent with DSS API requirement and does not require flipud
        _data = np.reshape(_data,shape)
        if _data.dtype != np.float32:
            _data = _data.astype(np.float32, order="C", casting="unsafe", copy=True)
            is_copied = True

    else:
        # data is 2D array
        if _data.dtype != np.float32:
            _data = _data.astype(np.float32, order="C", casting="unsafe", copy=True)
            is_copied = True

        if np.any(np.isnan(_data)):
            if make_copy and not is_copied:
                _data = _data.copy()
            nan_mask = np.isnan(_data)
            _data[nan_mask] = nodata
    
    # _data can have both UNDEFINED and nodata at this point

    if (not is_sgrid) and flipud:
        _data = np.flipud(_data)

    if not _data.flags["C_CONTIGUOUS"]:
        _data = np.ascontiguousarray(_data)
    
    def _compute_stats():
        data_count = _data.size

        if is_masked:
            filtered_data = _data[~mask]
        else:
            if is_nodata_undefined:
                filtered_data = _data[_data != UNDEFINED]
            else:
                filtered_data = _data[(_data != UNDEFINED) & (_data != nodata)]
        
        min_val = filtered_data.min()
        max_val = filtered_data.max()
        mean_val = filtered_data.mean()
        range_counts = [data_count]

        if isinstance(range_values,(list,tuple)):
            range_vals = [x for x in range_values]

        elif is_sgrid:
            range_vals = data.gridinfo.range_vals
        
        else:
            # compute range values as quartiles
            range_vals = list(np.percentile(filtered_data,[25,50,75]))
        
        range_vals = sorted([x for x in range_vals if not (np.isnan(x) or x < min_val or x > max_val) or x==nodata or x==UNDEFINED])
        range_vals = range_vals[0:20]
        range_vals.insert(0,UNDEFINED)
        for val in range_vals[1:]:
            cnt = (filtered_data >= val).sum()
            range_counts.append(cnt)
        
        stats = {
            "min_val": min_val,
            "max_val": max_val,
            "mean_val": mean_val,
            "range_vals": range_vals,
            "range_counts": range_counts
        }

        return stats
    
    stats = None
    if compute_stats:
        stats = _compute_stats()
    
    return _data,stats


def _process_pathname_pattern(pathname: Union[str, DssPathName]) -> str:
    """
    Process pathname pattern for catalog searches.

    Converts empty pathname parts (represented by //) to wildcards (*).

    Parameters
    ----------
    pathname : str or DssPathName
        Pathname or pattern to process.

    Returns
    -------
    str
        Processed pathname string with wildcards.

    Examples
    --------
    >>> _process_pathname_pattern("/A/B//D//F/")
    '/A/B/*/D/*/F/'
    """
    pathname_obj = DssPathName(pathname)
    return pathname_obj.text().replace("//", "/*/")
