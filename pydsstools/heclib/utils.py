import logging
import warnings
logger = logging.getLogger(__name__)
import numpy as np
import numpy.ma as ma
import math
from ..core.grid import BoundingBox
from ..core import (
    HecTime,
    DssStatusException,
    GranularityException,
    ArgumentException,
    DssLastError,
    squeeze_file,
)
from ..core import GRID_TYPE, GRID_DATA_TYPE, GRID_COMPRESSION_METHODS
from ..core import Open as _Open
from ..core import UNDEFINED, SHG_WKT, HRAP_WKT
import atexit
from affine import Affine

# Public functions from utils.pyx / core_heclib
from ..core import set_message_level, get_message_level
from ..core import set_program_name, heclib_version
from ..core import pd_size, copy_record_to
from ..core import delete_pathname, rename_pathname, get_grid_version
from ..core import copy_file, copy_file_to, convert_version, check_file

__all__ = [
    # DSS logging — new API
    "get_dss_logger",
    "Level",
    "Method",
    # DSS logging — legacy API (kept for backward compatibility)
    "dss_logging",
    # DSS types and helpers
    "HecTime",
    "DssStatusException",
    "GranularityException",
    "ArgumentException",
    "DssLastError",
    "compute_grid_stats",
    "grid_type_names",
    "grid_data_type_names",
    "UNDEFINED",
    "HRAP_WKT",
    "SHG_WKT",
    "BoundingBox",
    # utils.pyx public functions
    "set_message_level",
    "get_message_level",
    "set_program_name",
    "heclib_version",
    "squeeze_file",
    "pd_size",
    "copy_record_to",
    "delete_pathname",
    "rename_pathname",
    "get_grid_version",
    "copy_file",
    "copy_file_to",
    "convert_version",
    "check_file",
]

from .logging import Level, Method, get_dss_logger

# Legacy lookup tables kept for any code that imported them directly.
# New code should use the Level and Method enums from pydsstools.heclib.logging.
log_level = {
    0: "None",
    1: "Error",
    2: "Critical",
    3: "General",
    4: "Info",
    5: "Debug",
    6: "Diagnostic",
}

log_method = {
    0: "ALL",
    1: "VER7",
    2: "READ_LOWLEVEL",
    3: "WRITE_LOWLEVEL",
    4: "READ",
    5: "WRITE",
    6: "_",
    7: "OPEN",
    8: "CHECK_RECORD",
    9: "LOCKING",
    10: "READ_TS",
    11: "WRITE_TS",
    12: "ALIAS",
    13: "COPY",
    14: "UTILITY",
    15: "CATALOG",
    16: "FILE_INTEGRITY",
}

__dsslog = None


@atexit.register
def __close():
    if not __dsslog is None:
        try:
            __dsslog.close()
        except:
            logger.error("Error closing dsslog")
        else:
            logger.debug("dsslog file closed")


def __init():
    global __dsslog
    if not __dsslog is None:
        from os import path

        dss_file = path.join(path.dirname(__file__), dsslog.dss)
        logger.info("File used to intialize pydsstools messaging is %s", dss_file)
        __dsslog = _Open(dss_file)


__init()


class DssLogging(object):
    """Legacy interface for controlling DSS C library message verbosity.

    .. note::

        **Deprecated.** Use :func:`~pydsstools.heclib.logging.get_dss_logger`
        instead.  This class is retained for backward compatibility only; all
        calls delegate to the new :mod:`pydsstools.heclib.logging` module so
        that state stays consistent regardless of which API is used.

    Examples
    --------
    Old (still works, but raises :exc:`DeprecationWarning`)::

        from pydsstools.heclib.utils import dss_logging
        dss_logging.setLevel("General")
        dss_logging.config(method=9, level="Critical")

    New (preferred)::

        from pydsstools.heclib.logging import get_dss_logger, Level, Method
        get_dss_logger().set_level(Level.GENERAL)
        get_dss_logger(Method.LOCKING).set_level(Level.CRITICAL)
    """

    def setLevel(self, level):
        """Set the global (all-methods) DSS message level.

        .. note::

            **Deprecated.** Use ``get_dss_logger().set_level(level)`` from
            :mod:`pydsstools.heclib.logging` instead.

        Parameters
        ----------
        level:
            An integer DSS level (0–6), one of the legacy string names
            (``"None"``, ``"Error"``, ``"Critical"``, ``"General"``,
            ``"Info"``, ``"Debug"``, ``"Diagnostic"``), or any form
            accepted by :meth:`~pydsstools.heclib.logging.DssLogger.set_level`.
        """
        warnings.warn(
            "dss_logging.setLevel() is deprecated. "
            "Use get_dss_logger().set_level() from pydsstools.heclib.logging.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            get_dss_logger().set_level(level)
        except (ValueError, TypeError):
            logger.warning("Invalid DSS logging level ignored: %r", level)

    def config(self, method=0, level="Terse"):
        """Set the DSS message level for a specific method group.

        .. note::

            **Deprecated.** Use ``get_dss_logger(method).set_level(level)``
            from :mod:`pydsstools.heclib.logging` instead.

        Parameters
        ----------
        method:
            Integer method ID (0–16 in the legacy table) or any form
            accepted by :func:`~pydsstools.heclib.logging.get_dss_logger`.
        level:
            Verbosity level; accepts the same forms as
            :meth:`~pydsstools.heclib.logging.DssLogger.set_level`.
            Defaults to ``"Terse"`` to match the pydsstools library default.
        """
        warnings.warn(
            "dss_logging.config() is deprecated. "
            "Use get_dss_logger(method).set_level(level) from pydsstools.heclib.logging.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            get_dss_logger(method).set_level(level)
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid DSS logging config ignored: %s", exc)


dss_logging = DssLogging()

grid_data_type_names = tuple(GRID_DATA_TYPE.keys())
grid_type_names = tuple(GRID_TYPE.keys())


def compute_grid_stats(data, compute_range=True):
    """Compute statistical value for numpy array data for Spatial grid

    Parameter
    ---------
        # data: numpy array or masked array
        # compute_range: boolean, string or list of values
            # boolean - True, False
            # string - quartiles, quarters, TODO
            # list/tuple - list of values (max 19 excluding nodata) to compute equal to greater than cell counts
    """
    logger.info("Computing grid statistics")
    result = {
        "min": None,
        "max": None,
        "mean": None,
        "range_values": [],
        "range_counts": [],
    }
    total_cells = data.size

    if total_cells == 0:
        logger.info("Empty Grid Array!")
        return

    if isinstance(data, ma.core.MaskedArray):
        data = data[~data.mask]
        data = data._data
    elif isinstance(data, np.ndarray):
        data = data[~np.isnan(data)]
    else:
        raise Exception("Invalid data. Numpy or Masked Array expected.")

    min_value = data.min()
    max_value = data.max()
    mean_value = data.mean()

    result.update(
        [("min_val", min_value), ("max_val", max_value), ("mean_val", mean_value)]
    )
    # print(result)

    range_values = []
    if isinstance(compute_range, (list, tuple)):
        range_values = sorted(
            [
                x
                for x in compute_range
                if not (np.isnan(x) or x < min_value or x > max_value)
            ]
        )

    elif compute_range or isinstance(compute_range, str):
        # default range
        if min_value < 0 and max_value > 0:
            range_values = np.linspace(min_value, max_value, 10)
            range_values = range_values.tolist()
        else:
            q0 = min_value
            q1 = 0.25 * (min_value + max_value)
            q2 = 0.5 * (min_value + max_value)
            q3 = 0.75 * (min_value + max_value)
            range_values = [q0, q1, q2, q3]
        range_values = [round(x, 2) for x in range_values]
    else:
        pass

    range_values = range_values[0:19]
    range_values.insert(0, np.nan)
    range_counts = [total_cells]  # assuming no data is very small negative number
    # print(type(data),'data=',data,'\n')
    # print(range_values,range_counts)
    for val in range_values[1:]:
        count = (data >= val).sum()
        range_counts.append(count)

    result.update([("range_vals", range_values), ("range_counts", range_counts)])
    logger.info(result)
    return result