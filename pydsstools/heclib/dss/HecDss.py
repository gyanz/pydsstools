"""
Open class object for HEC-DSS file

This module provides the public API for interacting with HEC-DSS files.
"""

__all__ = ["Open"]

import logging
logger = logging.getLogger(__name__)
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
except ImportError:
    # python 3.9
    from typing_extensions import Annotated, TypeAlias, Literal

from ...core import Open as _Open
from ...core import TimeSeriesStruct, TimeSeriesContainer
from ...core import PairedDataStruct, PairedDataContainer
from ...core import SpatialGridStruct
from ...core import TextStruct, TextContainer
from ...core import BinaryStruct, BinaryContainer
from ...core import ArrayContainer
from ...core.enums import GridType, RegStoreFlag, IrregStoreFlag, BinaryType
from ...core.gridinfo import GridInfo
from ...core.gridinfo.v6 import gridinfo7_to_gridinfo6, GridInfo6
#from ...core.gridv6_internals import gridinfo7_to_gridinfo6, GridInfo6
from ...core import (
    PairedDataContainer,
    HecTime,
    DssPathName,
    UNDEFINED,
)
from ...core.location import LocationInfo

DateLike = TypeVar("DateLike", str, datetime, HecTime)
DateWindow: TypeAlias = tuple[DateLike, DateLike]
PathType: TypeAlias = Union[str, Path, PathLike]

_PRECISION_MAP: dict[str, int] = {"float": 1, "double": 2, "native": 0}


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
        if not isinstance(dss_path, (str, Path, PathLike)):
            raise TypeError(
                f"dss_path must be str, Path, or PathLike, got {type(dss_path).__name__}"
            )
        super().__init__(str(Path(dss_path)), version)
        self.mode = mode

    def read_ts(
        self,
        pathname: Union[str, DssPathName],
        window: Optional[DateWindow] = None,
        trim_missing: bool = False,
        window_flag: Literal[0, 1, 2, 3] = 0,
        value_precision: Literal["float", "double", "native"] = "float",
        quality_notes: bool = False,
        reg: Optional[bool] = False,
        ireg: Optional[bool] = False,
        location: Optional[bool] = None,
    ) -> Union[TimeSeriesStruct, tuple[TimeSeriesStruct, Optional[LocationInfo]]]:
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
        value_precision : {"float", "double", "native"}, optional
            Controls the numeric precision of the retrieved values. Default is "float".

            * "float"  : Return values as 32-bit floats.
            * "double" : Return values as 64-bit doubles.
            * "native" : Return values as stored; missing values returned as doubles.
        quality_notes : bool, optional
            If True, retrieve quality notes associated with each value when they exist.
            Default is False.
        reg : bool, optional
            If True, treat the data as a regular time series. Default is False.
        ireg : bool, optional
            If True, treat the data as an irregular time series. Default is False.

            If both ``reg`` and ``ireg`` are ``False`` or both are ``True``, the type of
            time series will be determined from the E-part of ``pathname``.

        location : bool or None, optional
            If True, also read the location record associated with the pathname
            and return ``(TimeSeriesStruct, LocationInfo)``.  If no location
            record exists a warning is logged and ``None`` is returned in its
            place.  Default is None (return TimeSeriesStruct only).

        Returns
        -------
        TimeSeriesStruct
            Time series data structure containing the requested data.
        tuple of (TimeSeriesStruct, LocationInfo or None)
            Returned when ``location=True``.

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

        Read time series and its location record together:

        >>> ts, loc = fid.read_ts(pathname, location=True)
        """
        pathname = DssPathName(pathname)

        if value_precision not in _PRECISION_MAP:
            raise ValueError(
                f"Invalid value_precision {value_precision!r}. "
                f"Must be one of: {list(_PRECISION_MAP)}"
            )
        retrieve_doubles = _PRECISION_MAP[value_precision]
        retrieve_quality = int(quality_notes)

        infer_type = True
        if reg and ireg:
            logger.info("The timeseries to be read is specified as both regular and irregular type; type will be inferred from the pathname.")
        elif reg:
            infer_type = False
            interval = 1
        elif ireg:
            infer_type = False
            interval = -1

        if infer_type:
            # find whether the ts is regular, irregular or not ts
            logger.debug("Determining the type of timeseries record.")
            interval = self._ts_type_from_pathname(pathname.text())

            if interval == 0:
                raise ValueError(
                    f"The pathname '{pathname.text()}' does not correspond to a valid "
                    f"regular or irregular time series record. Verify the E-part "
                    f"'{pathname.epart}' has a standard interval specification."
                )

        if interval == 1:
            logger.debug("Reading regular time series.")
            retrieve_flag = -1 if trim_missing else 0

        else:
            logger.debug("Reading irregular time series.")
            if window_flag in [0, 1, 2, 3]:
                retrieve_flag = window_flag
            else:
                logger.error("Invalid window_flag for irregular dss record")
                return

        if window:
            start_date, end_date = window
            sdate = HecTime(start_date, midnight_as_2400=False)
            edate = HecTime(end_date, midnight_as_2400=True)
            sday = sdate.date()
            stime = sdate.time(2)
            eday = edate.date()
            etime = edate.time(2)
            tss = super()._read_ts_window(
                pathname.text(), sday, stime, eday, etime, retrieve_flag,
                boolRetrieveDoubles=retrieve_doubles,
                boolRetrieveQualityNotes=retrieve_quality,
            )

        else:
            retrieve_all = 0
            if (
                not pathname.dpart.strip()
            ):  # if date part is empty, retrieve all data ignoring date
                retrieve_all = 1
            tss = super()._read_ts_normal(
                pathname.text(), retrieve_flag,
                boolRetrieveDoubles=retrieve_doubles,
                boolRetrieveQualityNotes=retrieve_quality,
                boolRetrieveAllTimes=retrieve_all,
            )

        if location:
            loc = None
            try:
                loc = super()._read_location(pathname.text())
            except Exception:
                logger.warning("No location record found for '%s'.", pathname.text())
            return tss, loc

        return tss


    def put_ts(
        self,
        data: Union[str, "DssPathName", "TimeSeriesContainer"],
        location: Optional[LocationInfo] = None,
        store_flag: Union[RegStoreFlag, IrregStoreFlag, int] = 0,
        **kwargs: Any,
    ) -> None:
        """
        Write time-series data to DSS file.

        Parameters
        ----------
        data : str or DssPathName or TimeSeriesContainer
            Either a pathname string or a TimeSeriesContainer object.
        location : LocationInfo or None, optional
            If provided, write this location record after writing the time series.
            Default is None.
        store_flag : RegStoreFlag or IrregStoreFlag or int, optional
            Controls how existing data is handled on write. Default is 0.

            For regular time series (use ``RegStoreFlag``):

            * 0 : Always replace data.
            * 1 : Only replace missing values.
            * 2 : Write even if all values are missing.
            * 3 : If all missing, do not write and delete record if it exists.
            * 4 : Do not allow a missing input value to replace a valid value.

            For irregular time series (use ``IrregStoreFlag``):

            * 0 : Merge — insert new values; replace existing values at the same time.
            * 1 : Replace — remove all data in the start-to-end range and rewrite.

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

        location : LocationInfo or None, optional
            If provided, write this location record to the DSS file immediately
            after writing the time series.  Default is None.

        Write irregular time series without using TimeSeriesContainer:

        >>> pathname = r"/A/B/C//IR-DAY/F/"
        >>> julian_base = "01JAN2000"
        >>> times = ["02JUL2010 1200", "05JAN2012 0000", "15MAR2014 0200",
        ...          "25FEB2018 0500", "19DEC2024 1200"]
        >>> values = [1, 20, 30, 40, 50]
        >>> fid.put_ts(pathname, values=values, times=times, julian_base=julian_base,
        ...            data_units=data_units, data_type=data_type, tzid=timezone)

        Write time series with location metadata:

        >>> from pydsstools.core.location import LocationInfo
        >>> loc = LocationInfo("/A/B/C//1HOUR/F/", x=-118.5, y=34.0)
        >>> fid.put_ts(tsc, location=loc)
        """

        if self.mode != "rw":
            logger.error(
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
                logger.warning("Ignoring pathname for TimeSeriesContainer provided as keyword argument")

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
                    logger.warning(f"Ignoring count argument value (={_count}) as it is not equal to the length of values (={count})")

            if interval < 0:
                # required for irregular time-series
                times = kwargs["times"]

            tsc = TimeSeriesContainer(pathname.text(), count, interval, **kwargs)

        _flag = int(store_flag)
        if tsc.interval > 0:
            valid = set(m.value for m in RegStoreFlag)
            if _flag not in valid:
                raise ValueError(
                    f"Invalid store_flag {_flag!r} for regular time series. "
                    f"Use RegStoreFlag or one of {sorted(valid)}."
                )
        else:
            valid = set(m.value for m in IrregStoreFlag)
            if _flag not in valid:
                raise ValueError(
                    f"Invalid store_flag {_flag!r} for irregular time series. "
                    f"Use IrregStoreFlag or one of {sorted(valid)}."
                )
        if tsc.quality_flags is not None and tsc._quality_elem_size > 1 and self.version == 6:
            raise ValueError(
                "DSS-6 supports only one quality integer per value "
                "(qualityElementSize must be 1). "
                "Use a 1-D array or a 2-D array with a single column."
            )
        if location is not None:
            if not isinstance(location, LocationInfo):
                raise TypeError(
                    f"Expected LocationInfo for location, got {type(location).__name__}"
                )
            # The pathname in put_ts (tsc.pathname) is authoritative.
            # loc.pathname is used only for metadata; it has no effect on which
            # DSS record the location is attached to.  For DSS-7, _put_location
            # keys the location record via zlocationPath(loc.pathname), so a
            # mismatch would write location to a different namespace.  Normalize
            # here so the caller never has to keep the two in sync.
            if location.pathname.text() != tsc.pathname:
                logger.warning(
                    "put_ts: loc.pathname %r differs from tsc.pathname %r; "
                    "using tsc.pathname for the location record",
                    location.pathname.text(), tsc.pathname,
                )
                location.pathname = DssPathName(tsc.pathname)

        if location is not None and self.version == 6:
            # DSS-6: location must be embedded inside the TS record.
            # ztsStore (used by _put) has no location fields in zStructTimeSeries,
            # and zlocationStore is DSS-7 only.  _put_dss6 calls zsrtsc_/zsitsc_
            # which write TS data and location in one Fortran call.
            super()._put_dss6(tsc, location, _flag)
        else:
            super()._put(tsc, _flag)
            if location is not None:
                super()._put_location(location)

    def read_pd(
        self,
        pathname: Union[str, "DssPathName"],
        window: Optional[tuple[int, int, int, int]] = None,
        dataframe: Optional[bool] = True,
        location: Optional[bool] = None,
    ) -> Union[pd.DataFrame, PairedDataStruct, tuple]:
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
        location : bool or None, optional
            If True, also read the location record associated with the pathname
            and return ``(result, LocationInfo)``.  If no location record exists
            a warning is logged and ``None`` is returned in its place.  Default
            is None (return data only).  DSS-6 files raise ``NotImplementedError``.

        Returns
        -------
        pandas.DataFrame or PairedDataStruct
            Paired data in the requested format.
        tuple of (pandas.DataFrame or PairedDataStruct, LocationInfo or None)
            Returned when ``location=True``.

        Raises
        ------
        IndexError
            If window indices are invalid or out of range.
        NotImplementedError
            If ``location=True`` and the file is DSS-6.

        Examples
        --------
        Read paired data with a window:

        >>> df = fid.read_pd(pathname, window=(2, 5, 0, None))

        Read all paired data:

        >>> df = fid.read_pd(pathname)

        Read as PairedDataStruct:

        >>> pds = fid.read_pd(pathname, dataframe=False)

        Read paired data and its location record together:

        >>> df, loc = fid.read_pd(pathname, location=True)
        """
        pathname = DssPathName(pathname)

        if window:
            logger.debug(f"Input paired data window = '{window}'")
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

            logger.debug(f"Updated window = '{window}'")

        pds = super()._read_pd(pathname.text(), window)
        result = pds

        if dataframe:
            x_data = pds.x_data
            y_data = pds.y_data
            y_labels = pds.y_labels
            logger.debug(y_labels)
            # The row in curves array contains curve data
            # Transpose causes the curve data to be in columns (for DataFrame purpose)
            tb = np.asarray(y_data).T
            if not window:
                _col_start = 0
                _col_end = tb.shape[1] - 1

            primary_colnames = [f"y{i}" for i in range(_col_start, _col_end + 1)]
            alias_colnames = ['' for x in range(_col_start, _col_end + 1)]

            logger.debug(f'window:{window}')
            logger.debug(f'col_start/end: {_col_start},{_col_end}')
            logger.debug(f'primary colnames: {primary_colnames}')
            logger.debug(f'alias columns: {alias_colnames}')

            for i, label in enumerate(y_labels):
                alias_colnames[i] = label

            logger.debug(f'Revised alias columns: {alias_colnames}')
            column_names = pd.MultiIndex.from_arrays([primary_colnames, alias_colnames], names=["primary", "labels"])

            indx = list(x_data[0])
            df = pd.DataFrame(
                data=tb, index=indx, columns=column_names, copy=True
            )
            df.index.name = "x_data"
            result = df

        if location:
            if self.version == 6:
                raise NotImplementedError(
                    "Location records are not supported for paired data in DSS-6 files."
                )
            loc = None
            try:
                loc = super()._read_location(pathname.text())
            except Exception:
                logger.warning("No location record found for '%s'.", pathname.text())
            return result, loc

        return result

    def read_pd_labels(self, pathname: Union[str, "DssPathName"]) -> dict[str, str]:
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

    def pd_info(self, pathname: Union[str, "DssPathName"]) -> dict[str, Any]:
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
        location: Optional[LocationInfo] = None,
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

        location : LocationInfo or None, optional
            If provided, write this location record after writing the paired data.
            DSS-7 only; DSS-6 files raise ``NotImplementedError``. Default is None.

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
            logger.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if location is not None:
            if not isinstance(location, LocationInfo):
                raise TypeError(
                    f"Expected LocationInfo for location, got {type(location).__name__}"
                )
            if self.version == 6:
                raise NotImplementedError(
                    "Location records are not supported for paired data in DSS-6 files."
                )

        if isinstance(data, PairedDataContainer):
            super()._put_pd(data)
            if location is not None:
                record_path = data.pathname
                if location.pathname.text() != record_path:
                    logger.warning(
                        "put_pd: loc.pathname %r differs from record pathname %r; "
                        "using record pathname for the location record",
                        location.pathname.text(), record_path,
                    )
                    location.pathname = DssPathName(record_path)
                super()._put_location(location)
            return

        if isinstance(data, (str, DssPathName)):
            pathname = DssPathName(data)
            y_data = kwargs.pop("y_data", None)
            col_index = kwargs.pop("col_index", None)

            if "pathname" in kwargs:
                logger.warning("Ignoring pathname for PairedDataContainer provided as keyword argument")

            if isinstance(y_data, pd.DataFrame):
                logger.info('Writing paired data from DataFrame')
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
                if location is not None:
                    record_path = pathname.text()
                    if location.pathname.text() != record_path:
                        logger.warning(
                            "put_pd: loc.pathname %r differs from record pathname %r; "
                            "using record pathname for the location record",
                            location.pathname.text(), record_path,
                        )
                        location.pathname = DssPathName(record_path)
                    super()._put_location(location)
                return

            elif isinstance(col_index, int):
                logger.info('Writing single paired data curve to preallocated paired data set')
                # pd_info raise error if the record does not exist
                size_info = self._pd_info(pathname.text())
                rows = size_info["data_no"]
                cols = size_info["curve_no"]
                logger.debug(f"The paired data record ({pathname.text()}) in file has rows={rows} and cols={cols}")

                # 1-based col_index
                logger.debug(f"Input 0-based col_index = {col_index}")
                col_index, _ = _normalize_span(cols, col_index, None)
                logger.debug(f"Updated 1-based col_index = {col_index}")

                # 1-based default indices
                row_start, row_end = (1, rows)
                logger.debug(f"1-based (row_start,row_end) assuming full curve data is replaced: ({row_start},{row_end}).")

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
                    logger.debug(f"0-based (row_start,row_end) provided as input: ({_row_start},{_row_end}).")
                    # 1-based
                    row_start, row_end = _normalize_span(rows, _row_start, _row_end)
                    logger.debug(f"1-based (row_start,row_end) derived from input: ({row_start},{row_end}).")

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
                    logger.warning("The y_data for single curve has multiple rows; flattening the data as single row of values.")
                    _y_data = np.ascontiguousarray(_y_data.reshape(1, -1))

                y_data = _y_data

                shape = (y_data.shape[1], 1)

                if shape[0] + row_start - 1 > rows:
                    raise IndexError("y_data has too many values exceeding allowable row_end index")

                # update  row_end based on number of y_data values
                if row_end != row_start + shape[0] - 1:
                    logger.debug("row_end updated based on the number of y_data")
                    row_end = row_start + shape[0] - 1

                logger.debug(f"Single paired data curve to be written with 1-based row_start={row_start} and row_end={row_end}. Total rows in dss = {rows}.")
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
                if location is not None:
                    record_path = pathname.text()
                    if location.pathname.text() != record_path:
                        logger.warning(
                            "put_pd: loc.pathname %r differs from record pathname %r; "
                            "using record pathname for the location record",
                            location.pathname.text(), record_path,
                        )
                        location.pathname = DssPathName(record_path)
                    super()._put_location(location)
                return

        raise ValueError('Incompatible input parameters provided to write paired data to dss file')


    def preallocate_pd(
        self,
        pathname: Union[str, "DssPathName"],
        shape: Union[list[int], tuple[int, int]],
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
            logger.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname = DssPathName(pathname)
        pdc = PairedDataContainer(pathname.text(), shape, **kwargs)
        super()._prealloc_pd(pdc)

    # ------------------------------------------------------------------ array --

    def read_array(
        self,
        pathname: Union[str, "DssPathName"],
    ) -> dict:
        """Read an array record from the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.

        Returns
        -------
        dict
            Dictionary with any of the following keys, depending on what was
            stored:

            * ``'int_array'`` : numpy.ndarray of int32
            * ``'float_array'`` : numpy.ndarray of float32
            * ``'double_array'`` : numpy.ndarray of float64

        Examples
        --------
        >>> result = fid.read_array("/A/B/COUNTS/D/E/F/")
        >>> int_vals = result.get('int_array')
        >>> float_vals = result.get('float_array')
        """
        pathname = DssPathName(pathname)
        arr_st = super()._read_array(pathname.text())
        result = {}
        if arr_st.int_array is not None:
            result['int_array'] = np.array(arr_st.int_array)
        if arr_st.float_array is not None:
            result['float_array'] = np.array(arr_st.float_array)
        if arr_st.double_array is not None:
            result['double_array'] = np.array(arr_st.double_array)
        return result

    def put_array(
        self,
        pathname: Union[str, "DssPathName"],
        *,
        int_array: Optional[npt.ArrayLike] = None,
        float_array: Optional[npt.ArrayLike] = None,
        double_array: Optional[npt.ArrayLike] = None,
    ) -> None:
        """Write an array record to the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        int_array : array-like or None, optional
            Integer values to store. Converted to int32.
        float_array : array-like or None, optional
            Float values to store. Converted to float32.
        double_array : array-like or None, optional
            Double values to store. Converted to float64.

        Notes
        -----
        At least one of the three array arguments must be provided.

        Examples
        --------
        >>> import numpy as np
        >>> fid.put_array("/A/B/COUNTS/D/E/F/", int_array=[1, 2, 3])
        >>> fid.put_array("/A/B/DATA/D/E/F/", float_array=np.array([1.0, 2.0]),
        ...               double_array=np.array([3.14, 2.72]))
        """
        if self.mode != "rw":
            logger.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return
        pathname = DssPathName(pathname)
        arr = ArrayContainer(
            pathname.text(),
            int_array=int_array,
            float_array=float_array,
            double_array=double_array,
        )
        super()._put_array(arr)

    # ------------------------------------------------------------------- text --

    def read_text(
        self,
        pathname: Union[str, "DssPathName"],
    ) -> "TextStruct":
        """Read a text or text-table record from the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.

        Returns
        -------
        TextStruct
            Structure wrapping the raw C record.  Applicable to both plain
            text and text-table records.

            Key properties:

            * ``text`` : str or None — plain text content.
            * ``table`` : list of list of str, or None — table content.
              Outer list is rows, inner list is columns.
            * ``labels`` : list of str — column labels (empty list if none).
            * ``rows`` : int — number of table rows (0 for text-only records).
            * ``cols`` : int — number of table columns (0 for text-only).
            * ``dtype`` : str or None — one of ``'text'``, ``'text_list'``,
              ``'text_table'``, or ``None``.

        Examples
        --------
        >>> ts = fid.read_text("/A/B/NOTE/D/E/F/")
        >>> ts.text
        'some note'
        >>> ts = fid.read_text("/A/B/COLORS-PROPS/D/E/F/")
        >>> ts.table
        [['Red', 'long'], ['Blue', 'short']]
        >>> ts.rows, ts.cols
        (2, 2)
        """
        pathname = DssPathName(pathname)
        return super()._read_text(pathname.text())

    def put_text(
        self,
        pathname: Union[str, "DssPathName"],
        data: Union[TextContainer, TextStruct, "pd.DataFrame"],
    ) -> None:
        """Write a text or text-table record to the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.
        data : TextContainer or TextStruct or pandas.DataFrame
            Content to write.  The ``text``, ``table``, and ``labels``
            properties are read from the object and control which C-level
            write function is called:

            * text only → plain text record (DSS-6 and DSS-7).
            * table only → text-table record (DSS-7 only).
            * text and table → combined record (DSS-7 only).

            Passing a ``TextStruct`` returned by ``read_text`` allows
            round-trip reads and writes without unpacking.

            Passing a ``pandas.DataFrame`` saves it as a text table (DSS-7
            only).  Column names become the table labels.  Numeric columns
            are converted to strings using ``float32`` → 7 significant
            figures and ``float64`` → 15 significant figures (``g`` format,
            trailing zeros stripped).  ``NaN`` values become ``""``.

        Raises
        ------
        TypeError
            If ``data`` is not a ``TextContainer``, ``TextStruct``, or
            ``pandas.DataFrame``.
        ValueError
            If the data has no text or table content, or if the DSS file
            version does not support the requested record type.

        Examples
        --------
        Plain text (DSS-6 or DSS-7):

        >>> fid.put_text("/A/B/NOTE/D/E/F/", TextContainer("/A/B/NOTE/D/E/F/", text="Hello"))

        Text list (DSS-7 only):

        >>> tc = TextContainer("/A/B/COLORS/D/E/F/", table=[["Red"], ["Blue"], ["Yellow"]])
        >>> fid.put_text("/A/B/COLORS/D/E/F/", tc)

        Full table with labels (DSS-7 only):

        >>> tc = TextContainer(
        ...     "/A/B/COLORS-PROPS/D/E/F/",
        ...     table=[["long", "hot"], ["short", "cool"]],
        ...     labels=["wave length", "temperature"],
        ... )
        >>> fid.put_text("/A/B/COLORS-PROPS/D/E/F/", tc)

        Round-trip via TextStruct:

        >>> ts = fid.read_text("/A/B/NOTE/D/E/F/")
        >>> fid2.put_text("/A/B/NOTE/D/E/F/", ts)

        DataFrame (DSS-7 only):

        >>> import pandas as pd
        >>> df = pd.DataFrame({"Color": ["Red", "Blue"], "Wavelength": [700.0, 450.0]})
        >>> fid.put_text("/A/B/COLORS/D/E/F/", df)
        """
        if isinstance(data, pd.DataFrame):
            rows, labels = _dataframe_to_table(data)
            data = TextContainer(
                DssPathName(pathname).text(), table=rows, labels=labels
            )
        if not isinstance(data, (TextContainer, TextStruct)):
            raise TypeError(
                f"data must be a TextContainer, TextStruct, or DataFrame, "
                f"got {type(data).__name__}"
            )
        if self.mode != "rw":
            logger.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return

        text = data.text
        table = data.table
        labels = data.labels
        pathname = DssPathName(pathname)
        data_pathname = data.pathname
        if data_pathname and DssPathName(data_pathname).text() != pathname.text():
            logger.warning(
                "put_text: pathname argument %r differs from data pathname %r; "
                "writing to %r",
                pathname.text(), data_pathname, pathname.text(),
            )

        if text is not None and table is not None:
            if self.version == 6:
                raise ValueError(
                    "DSS-6 does not support combined text+table records. "
                    "Use text-only content for DSS-6 files."
                )
            table_bytes, nrows, ncols, labels_bytes = _pack_table(table, labels)
            text_bytes = text.encode("ascii") + b"\x00"
            super()._put_text_combined(
                pathname.text(),
                text_bytes, len(text_bytes),
                table_bytes, nrows, ncols,
                labels_bytes,
            )
        elif table is not None:
            if self.version == 6:
                raise ValueError(
                    "DSS-6 does not support text table records. "
                    "Use text-only content for DSS-6 files."
                )
            table_bytes, nrows, ncols, labels_bytes = _pack_table(table, labels)
            super()._put_text_table(pathname.text(), table_bytes, nrows, ncols, labels_bytes)
        elif text is not None:
            super()._put_text_string(pathname.text(), text)
        else:
            raise ValueError("data has no text or table content")

    # ----------------------------------------------------------------- binary --

    def read_binary(
        self,
        pathname: Union[str, "DssPathName"],
    ) -> "BinaryStruct":
        """Read a binary (FILE, IMAGE, or BLOB) record from the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.

        Returns
        -------
        BinaryStruct
            Structure wrapping the raw C record.

            Key properties:

            * ``data`` : bytes — raw binary content, exact byte count.
            * ``filename`` : str — filename from the C-part of the pathname.
            * ``extension`` : str — file extension from the E-part (no dot).
            * ``data_type`` : BinaryType — FILE, IMAGE, or UNDEFINED.
            * ``is_image`` : bool — True for IMAGE records.
            * ``size`` : int — byte count.
            * ``save_to(path)`` — write bytes to a file; returns Path.

        Examples
        --------
        >>> bs = fid.read_binary("/a/b/report.pdf/FILE/pdf/f/")
        >>> bs.data
        b'%PDF-1.4 ...'
        >>> bs.filename
        'report.pdf'
        >>> bs.data_type
        <BinaryType.FILE: 600>
        """
        pathname = DssPathName(pathname)
        return super()._read_binary(pathname.text())

    def put_binary(
        self,
        pathname: Union[str, "DssPathName"],
        data: Union["BinaryContainer", "BinaryStruct", bytes],
        *,
        data_type: Optional["BinaryType"] = None,
    ) -> None:
        """Write a binary record to the DSS file.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname.  D-part is forced to match data_type.
        data : BinaryContainer or BinaryStruct or bytes
            Content to write.  When *data* is a ``BinaryContainer`` or
            ``BinaryStruct`` the embedded data and data_type are used
            directly.  When *data* is ``bytes``, the record is constructed
            from *pathname* and optional *data_type*.
        data_type : BinaryType or None, optional
            Override only when *data* is ``bytes``.  If None the type is
            inferred from the D-part or E-part of *pathname*.  Ignored when
            *data* is ``BinaryContainer`` or ``BinaryStruct``.

        Raises
        ------
        TypeError
            If *data* is not a BinaryContainer, BinaryStruct, or bytes.

        Examples
        --------
        >>> fid.put_binary("/a/b/report.pdf/FILE/pdf/f/", pdf_bytes)
        >>> fid.put_binary("/a/b/photo.jpg/IMAGE/jpg/f/", jpeg_bytes,
        ...                data_type=BinaryType.IMAGE)
        >>> container = BinaryContainer("/a/b/report.pdf/FILE/pdf/f/", pdf_bytes)
        >>> fid.put_binary("/a/b/report.pdf/FILE/pdf/f/", container)
        """
        if self.mode != "rw":
            logger.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return
        pathname = DssPathName(pathname)
        if isinstance(data, BinaryContainer):
            container = data
        elif isinstance(data, BinaryStruct):
            container = BinaryContainer(
                pathname.text(), data.data, data_type=data.data_type
            )
        elif isinstance(data, (bytes, bytearray)):
            container = BinaryContainer(
                pathname.text(), data, data_type=data_type
            )
        else:
            raise TypeError(
                "data must be a BinaryContainer, BinaryStruct, or bytes, "
                "got {!r}".format(type(data).__name__)
            )
        data_pathname = container.pathname
        if DssPathName(data_pathname).text() != pathname.text():
            logger.warning(
                "put_binary: pathname argument %r differs from container pathname %r; "
                "writing to %r",
                pathname.text(), data_pathname, pathname.text(),
            )
            container = BinaryContainer(pathname.text(), container.data,
                                        data_type=container.data_type)
        super()._put_binary(container)

    def export_binary(
        self,
        pathname: Union[str, "DssPathName"],
        output_dir: Union[str, Path] = ".",
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Read a binary record and save it to a file on disk.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS record pathname to read.
        output_dir : str or Path, optional
            Directory to write to.  The filename is taken from the C-part of
            *pathname*.  Defaults to the current directory.
        output_path : str or Path, optional
            Full destination path.  When given, *output_dir* is ignored.

        Returns
        -------
        Path
            Path to the written file.

        Examples
        --------
        >>> dest = fid.export_binary("/a/b/report.pdf/FILE/pdf/f/",
        ...                          output_dir="C:/output")
        >>> dest
        PosixPath('C:/output/report.pdf')
        """
        bs = self.read_binary(pathname)
        if output_path is not None:
            dest = Path(output_path)
        else:
            if not bs.filename:
                raise ValueError(
                    f"Cannot derive a filename from pathname {str(pathname)!r} (C-part is empty). "
                    "Pass output_path explicitly."
                )
            dest = Path(output_dir) / bs.filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(bs.data)
        return dest

    def import_binary(
        self,
        filepath: Union[str, Path],
        pathname: Optional[str] = None,
        *,
        a: str = "",
        b: str = "",
        f: str = "",
    ) -> None:
        """Read a file from disk and store it as a binary DSS record.

        The data_type and D-part are always derived automatically from the
        file extension; known image extensions yield BinaryType.IMAGE (610),
        all other extensions yield BinaryType.FILE (600).

        Parameters
        ----------
        filepath : str or Path
            Path to the file to import.
        pathname : str or None, optional
            DSS pathname to store under.  If None, an auto-built pathname is
            used: C-part = filename, D-part = ``'IMAGE'`` or ``'FILE'``,
            E-part = extension without dot.
        a, b, f : str
            A, B, F parts of the auto-built pathname (used only when
            *pathname* is None).

        Examples
        --------
        >>> fid.import_binary("C:/reports/summary.pdf", b="ProjectX")
        >>> fid.import_binary("C:/photos/site.jpg")
        """
        if self.mode != "rw":
            logger.error("Open the dss file in 'rw' mode to be able to write data on it.")
            return
        container = BinaryContainer.from_file(filepath, pathname=pathname,
                                              a=a, b=b, f=f)
        super()._put_binary(container)

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
           There are slight differences in grid metadata between version-0 and version-100 grids. For example, the RLE-style compression 
           used for precipitation data is supported only in version-0 grids. When a version-0 grid is read using ``read_grid``, this 
           compression method is reported in the returned ``gridinfo`` as *undefined compression*. Consequently, if a version-0 grid 
           needs to be read and written back while preserving its original format, the ``read_grid2`` method should be used instead.
        """
        pathname = DssPathName(pathname)
        sg_st = SpatialGridStruct()
        retrieve_data = False if metadata_only else True
        grid_ver = self._get_gridver(pathname.text())

        if grid_ver is None:
            logger.error("Invalid grid data or version")
            return

        elif grid_ver == 100:
            logger.info("Reading modern format (DSS7) grid")
            super()._read_grid100(pathname.text(), sg_st, retrieve_data)

        else:
            logger.info(
                "Read grid version {} and convert it to version 100 grid".format(
                    grid_ver
                )
            )

            #if self.version == 7:
            #    raise NotImplementedError("Reading version {} from from DSS7 file is not implemented.", grid_ver)

            # find grid_type and create gridinfo6
            grid_type = self._get_gridtype(pathname.text())
            logger.debug("grid type is {}".format(grid_type))
            gridinfo6 = GridInfo6.from_grid_type(grid_type)
            logger.debug("grid type in gridinfo6 is {}".format(gridinfo6.grid_type))
            if grid_type == 430:
                # add space for crs definition, tz id generously
                # it should be more than what is in the file
                gridinfo6 = GridInfo6.get_specinfo6(50, 200, 50)
                logger.debug(
                    "grid type in updated gridinfo6 is {}".format(gridinfo6.grid_type)
                )
            super()._read_grid0(pathname.text(), sg_st, gridinfo6, retrieve_data)

        return sg_st

    def read_grid2(
        self, pathname: Union[str, "DssPathName"], metadata_only: Optional[bool] = False
    ) -> Optional[Union[tuple[np.ndarray, GridInfo], GridInfo]]:
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
            logger.error("Invalid grid data or version")
        elif grid_ver != 0:
            logger.info("Reading modern format (DSS7) grid")
            ds = self.read_grid(pathname.text(), retrieve_data)
            if metadata_only:
                logger.info("Returning metadata of gridded data")
                return ds.gridinfo
            else:
                return ds.read(), ds.gridinfo
        else:
            logger.info("Reading older format (DSS6 or grid version 0) grid")

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
                logger.info("Returning metadata of gridded data")
                if data is not None:
                    return gridinfo6
            if data is not None:
                logger.info("Returning metadata/data of gridded data")
                return data, gridinfo6

    def put_grid(
        self,
        data: Union["SpatialGridStruct", np.ndarray],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[GridInfo] = None,
        flipud: Optional[bool] = True,
        inplace: Optional[bool] = False,
        compute_stats: Optional[Union[bool, list[float]]] = True,
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
            logger.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 6:
            logger.warning("Writing DSS grid record in DSS-6 file is not supported")
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
                logger.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logger.error(
                    "Provide valid pathname for grid record!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)

        # Verify pathname has valid datetime stamps when grid is specified to have time component
        if gridinfo.has_time():
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

        logger.debug(f"{gridinfo}")
        super()._put_grid(pathname.text(), _data, gridinfo)

    def put_grid0(
        self,
        data: Union["SpatialGridStruct", np.ndarray],
        pathname: Optional[Union[str, "DssPathName"]] = None,
        gridinfo: Optional[Union[GridInfo, GridInfo6]] = None,
        flipud: Optional[bool] = True,
        inplace: Optional[bool] = False,
        compute_stats: Optional[Union[bool, list[float]]] = True,
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
            logger.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        if self.version == 7:
            logger.warning(
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
                logger.error("GridInfo is not provided to write gridded dataset")
                return

            if pathname is None:
                logger.error(
                    "Provide valid pathname for grid record!", exc_info=True
                )
                return

            pathname = DssPathName(pathname)

            # convert to gridinfo from verion 0 or 6 to 7, which is easier to work with
            if isinstance(gridinfo, GridInfo6):
                gridinfo = gridinfo.to_gridinfo7()

        # Verify pathname has valid datetime stamps when grid is specified to have time component
        if gridinfo.has_time():
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
            logger.error(
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
            logger.error(
                "Open the dss file in 'rw' mode to be able to write data on it."
            )
            return

        pathname_pattern = _process_pathname_pattern(pathname)
        pathlist = self.search_path(pathname_pattern)
        for pth in pathlist:
            status = self._delete_pathname(pth)

    def search_path(
        self, pathname: Union[str, "DssPathName"] = "", sort: Optional[bool] = False
    ) -> list[str]:
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
        path_list = []
        if pathname:
            pathname = _process_pathname_pattern(pathname)

        catalog = self._get_catalog(pathname, sort)
        if catalog is not None:
            path_list = catalog.paths()
        return path_list

    def path_exists(self, pathname: Union[str, "DssPathName"]) -> bool:
        """Check if a DSS pathname exists in the file.

        For pathnames whose D-part and E-part both contain a date and time
        component (e.g. ``2 June 2026:0000``), both parts are normalized before
        the lookup: the D-part expresses midnight as ``0000`` of the current
        day and the E-part expresses midnight as ``2400`` of the previous day.
        This resolves day-boundary ambiguity without changing non-datetime parts
        (interval names, empty parts, etc.).

        .. note::
            DSS stores grid D-part and E-part dates internally using
            ``date_style=2`` (HecTime), which produces the format
            ``"2 June 2026"`` — e.g. ``"2 June 2026:1400"``.  Normalization
            here uses the same style so the lookup pathname matches exactly
            what is stored on disk.

        Parameters
        ----------
        pathname : str or DssPathName
            DSS pathname to check.

        Returns
        -------
        bool
            True if the record exists, False otherwise.

        Examples
        --------
        >>> fid.path_exists("/A/B/PRECIP/1 January 2020:0000/1 January 2020:2400/F/")
        True

        >>> # Day-boundary variant is normalized before lookup
        >>> fid.path_exists("/A/B/PRECIP/31 December 2019:2400/1 January 2020:2400/F/")
        True
        """
        path = DssPathName(pathname)
        if ':' in path.dpart and ':' in path.epart:
            logger.debug("path_exists(): normalizing pathname: %s", path.text())
            path = path.normalize_period(date_style=2, time_style=0)
            logger.debug("path_exists(): normalized pathname:  %s", path.text())
        result = super()._path_exists(path.text())
        logger.debug("path_exists(): %s -> %s", path.text(), result)
        return result

    def path_dict(self, sub_type: Optional[bool] = False) -> dict[str, list[str]]:
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
            logger.debug(f"{path} is record type {name}.")
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
) -> tuple[int, int]:
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
    is_nodata_undefined = np.float32(nodata) == np.float32(UNDEFINED)

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
        _undef_f32 = np.float32(UNDEFINED)
        _nodata_f32 = np.float32(nodata)
        data_count = _data.size

        if is_masked:
            filtered_data = _data[~mask]
        else:
            if is_nodata_undefined:
                filtered_data = _data[_data != _undef_f32]
            else:
                filtered_data = _data[(_data != _undef_f32) & (_data != _nodata_f32)]

        if filtered_data.size == 0:
            min_val = UNDEFINED
            max_val = UNDEFINED
            mean_val = UNDEFINED
        else:
            min_val = filtered_data.min()
            max_val = filtered_data.max()
            mean_val = filtered_data.mean(dtype=np.float64)

        range_counts = [data_count]

        if isinstance(range_values,(list,tuple)):
            range_vals = [x for x in range_values]
            logger.debug("range_vals from user-supplied list: %s", range_vals)

        elif is_sgrid:
            range_vals = data.gridinfo.range_vals
            logger.debug("range_vals from gridinfo: %s", range_vals)

        else:
            # compute range values as quartiles + mean
            if filtered_data.size == 0:
                range_vals = []
            else:
                range_vals = list(np.percentile(filtered_data,[25,50,75]))
                if mean_val is not None and not np.isnan(mean_val):
                    range_vals.append(mean_val)
            logger.debug("range_vals from quartiles + mean: %s", range_vals)

        range_vals = sorted(set([
            x for x in range_vals
            if not (np.isnan(x) or x < min_val or x > max_val)
            or np.float32(x) == _nodata_f32
            or np.float32(x) == _undef_f32
        ]))

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
        logger.debug("compute_stats: %s", stats)

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


def _dataframe_to_table(df: "pd.DataFrame"):
    """Convert a DataFrame to (rows, labels) suitable for TextContainer.

    Column names become labels.  Per-column conversion:
      - float32  : f"{v:.7g}"  (7 significant figures, trailing zeros stripped)
      - float64  : f"{v:.15g}" (15 significant figures, trailing zeros stripped)
      - integer  : str(int(v))
      - boolean  : str(v)
      - other    : str(v)
    NaN / None values become "".

    Raises ValueError for MultiIndex columns or an empty DataFrame.
    """
    if isinstance(df.columns, pd.MultiIndex):
        raise ValueError("DataFrame with MultiIndex columns is not supported")
    if df.empty:
        raise ValueError("DataFrame must have at least one row and one column")

    labels = list(df.columns.astype(str))

    def _convert_col(series):
        kind = series.dtype.kind
        result = []
        for v in series:
            if kind == 'f':
                if pd.isna(v):
                    result.append("")
                elif series.dtype == np.float32:
                    result.append(f"{v:.7g}")
                else:
                    result.append(f"{v:.15g}")
            elif kind in ('i', 'u'):
                result.append(str(int(v)))
            elif kind == 'b':
                result.append(str(v))
            else:
                result.append("" if pd.isna(v) else str(v))
        return result

    columns = [_convert_col(df[col]) for col in df.columns]
    rows = [list(row) for row in zip(*columns)]
    return rows, labels


def _pack_table(table, labels):
    """Pack table rows and optional labels into null-delimited byte strings.

    Returns (table_bytes, nrows, ncols, labels_bytes).
    """
    if isinstance(table, np.ndarray):
        if table.ndim != 2:
            raise ValueError(
                f"numpy table array must be 2-dimensional, got {table.ndim}d"
            )
        if table.dtype.kind == 'S':
            table = [[cell.decode("ascii") for cell in row] for row in table]
        else:
            table = [[str(cell) for cell in row] for row in table]
    nrows = len(table)
    if nrows == 0:
        raise ValueError("table must have at least one row")
    ncols = len(table[0])
    if ncols == 0:
        raise ValueError("table must have at least one column")
    for i, row in enumerate(table):
        if len(row) != ncols:
            raise ValueError(
                f"all rows must have the same number of columns: "
                f"row 0 has {ncols}, row {i} has {len(row)}"
            )
    cells = []
    for row in table:
        for cell in row:
            cells.append(cell.encode("ascii"))
    table_bytes = b"\x00".join(cells) + b"\x00"
    labels_bytes = b""
    if labels:
        labels_bytes = b"\x00".join(lbl.encode("ascii") for lbl in labels) + b"\x00"
    return table_bytes, nrows, ncols, labels_bytes
