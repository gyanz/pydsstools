"""Control how much the HEC-DSS C library prints to the console.

Overview
--------
When pydsstools opens, reads, or writes DSS files the underlying HEC-DSS C
library prints status lines to the console — for example::

    -----DSS---zopen   Existing file opened, File: mydata.dss
    -----DSS---zwrite  Handle 1; Version 7: /Basin/Gauge/Flow/...

By default pydsstools keeps this output minimal (open/close events and errors
only).  This module lets you increase verbosity for debugging or silence
output entirely, using a :func:`get_dss_logger` factory modelled on Python's
own :func:`logging.getLogger`.

Each DSS operation belongs to a *method group* (e.g. ``TS_READ``, ``LOCKING``)
and each group has its own verbosity *level*.  Setting the ``GLOBAL`` group
applies the level to every group at once.

Quick start
-----------
::

    from pydsstools.heclib.logging import get_dss_logger, Level, Method

    # Increase verbosity for all operations (TERSE is the pydsstools default)
    get_dss_logger().set_level(Level.GENERAL)

    # Reduce verbosity for one noisy group while leaving others unchanged
    get_dss_logger(Method.LOCKING).set_level(Level.CRITICAL)

    # Silence all DSS output permanently
    get_dss_logger().set_level(Level.NONE)

    # Silence all DSS output for a block only, restore the previous level on exit
    with get_dss_logger().suppress():
        fid.read_ts(pathname)

    # Temporarily raise verbosity for a block, restore on exit
    with get_dss_logger(Method.TS_READ).at_level(Level.USER_DIAG):
        fid.read_ts(pathname)

    # Query the current level for a group
    logger = get_dss_logger(Method.TS_READ)
    print(logger.level)   # Level.TERSE
    print(logger)         # DssLogger(TS_READ, level=TERSE)

Python :mod:`logging` integers and name strings are also accepted by
:meth:`~DssLogger.set_level`, so existing logging configuration can be
forwarded directly::

    import logging
    get_dss_logger().set_level(logging.WARNING)      # → Level.TERSE
    get_dss_logger("ts_write").set_level("debug")    # → Level.USER_DIAG

Level mapping from Python logging integers
------------------------------------------
Python's :mod:`logging` levels run in the *opposite* direction to DSS levels:
a higher Python integer means more severe (less output), while a higher DSS
integer means more verbose (more output).  The mapping is:

=========================  =====  ===================  =====
Python logging constant    int    DSS Level            int
=========================  =====  ===================  =====
``logging.CRITICAL``        50    ``Level.CRITICAL``    1
``logging.ERROR``           40    ``Level.CRITICAL``    1
``logging.WARNING``         30    ``Level.TERSE``       2
``logging.INFO``            20    ``Level.GENERAL``     3
``logging.DEBUG``           10    ``Level.USER_DIAG``   4
``logging.NOTSET``           0    ``Level.GENERAL``     3
=========================  =====  ===================  =====

Developer notes
---------------
**Calling set_level before zopen is safe.**  ``zdssMessages.h`` warns that
``zsetMessageLevel`` should only be called after an initialising function such
as ``zopen``, and suggests using ``zset("mess", ...)`` beforehand.  In
practice this warning is outdated: ``zsetMessageLevel`` (and ``zset``) both
call ``zinit()`` internally when the library has not yet been initialised.
``zinit()`` itself is idempotent — it checks ``zdssVals.integrityKey`` and
returns immediately on any call after the first (``zinit.c`` lines 85-90).
Consequently, levels configured before the first ``zopen`` are preserved when
``zopen`` later triggers ``zinit()``, which becomes a no-op at that point.

**Why** ``zset("mess", ...)`` **was recommended for the pre-init case.**
When passed an empty ``charVal`` (method name), ``zset`` converts the integer
argument from the old DSS-6 ``mlvl`` scale (where 4 = normal, 10+ =
diagnostic) to the current DSS-7 scale (0-6) before forwarding to
``zsetMessageGroupLevel``.  ``zsetMessageLevel`` takes DSS-7 integers
directly, so there is no scale mismatch when this module passes our
``Level`` enum values (0-6).

**GLOBAL vs GENERAL — prefer GLOBAL.**  Both ``Method.GLOBAL`` (0) and
``Method.GENERAL`` (1) cause the C library to copy the level to all 18
``zmessaging.methodLevel`` slots (``zsetMessageLevel.c`` lines 107-111).
The difference is that ``GLOBAL`` additionally calls ``zset6_("MLVL", ...)``
which propagates the level to the DSS-6 Fortran messaging layer, making it
effective for DSS-6 files opened with ``zopen6`` as well.  ``GENERAL`` only
covers DSS-7.  For this reason :func:`get_dss_logger` returns the ``GLOBAL``
logger when called with no argument.  The ``level`` property reads back from C
via ``zgetMessageLevel`` so it always reflects the fan-out correctly for both
methods.
"""

from __future__ import annotations

import logging as _logging
from contextlib import contextmanager
from enum import IntEnum
from typing import Union

from ..core import setMessageLevel as _setMessageLevel
from ..core import getMessageLevel as _getMessageLevel

__all__ = [
    "Level",
    "Method",
    "DssLogger",
    "get_dss_logger",
]


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------

class Level(IntEnum):
    """Verbosity levels for the DSS C library messaging system.

    Values run from 0 (silent) to 6 (full trace).  Levels 1-3 produce
    Unicode output; levels 4+ are ASCII (hardwired in the C library).

    Several aliases are provided so that Python :mod:`logging` names can be
    used without a lookup table:

    * ``Level.ERROR``   is an alias for ``Level.CRITICAL``  (both == 1)
    * ``Level.WARNING`` is an alias for ``Level.TERSE``      (both == 2)
    * ``Level.INFO``    is an alias for ``Level.GENERAL``    (both == 3)
    * ``Level.DEBUG``   is an alias for ``Level.USER_DIAG``  (both == 4)

    These aliases satisfy ``Level.WARNING is Level.TERSE`` because
    :class:`~enum.IntEnum` treats duplicate values as canonical aliases.
    """

    NONE = 0
    """No messages at all (including errors). Strongly discouraged."""

    NULL = 0
    """Alias for :attr:`NONE`."""

    CRITICAL = 1
    """Error messages only."""

    ERROR = 1
    """Alias for :attr:`CRITICAL` (matches Python :data:`logging.ERROR` name)."""

    TERSE = 2
    """Minimal output: open/close events and critical errors."""

    WARNING = 2
    """Alias for :attr:`TERSE` (matches Python :data:`logging.WARNING` name)."""

    GENERAL = 3
    """General log messages: writes, reads, and housekeeping.

    The HEC-DSS C library initialises all groups to this level.  pydsstools
    overrides it to :attr:`TERSE` at import time via :attr:`Method.GLOBAL`.
    """

    INFO = 3
    """Alias for :attr:`GENERAL` (matches Python :data:`logging.INFO` name)."""

    USER_DIAG = 4
    """Diagnostic messages including input parameters.  ASCII output only."""

    DEBUG = 4
    """Alias for :attr:`USER_DIAG` (matches Python :data:`logging.DEBUG` name)."""

    INTERNAL_DIAG_1 = 5
    """Internal debug messages (level 1).  Not recommended for end-users."""

    INTERNAL_DIAG_2 = 6
    """Full internal trace (level 2).  Extremely verbose."""


# ---------------------------------------------------------------------------
# Method
# ---------------------------------------------------------------------------

class Method(IntEnum):
    """DSS C library method (operation) groups.

    Each group controls a category of operations independently.
    Names and integer IDs match the ``MESS_METHOD_*_ID`` constants in
    ``zdssMessages.h``.

    Pass a :class:`Method` value, its integer ID, or its name (case-insensitive
    string) to :func:`get_dss_logger`.
    """

    GLOBAL = 0
    """Blanket verbosity control for all method groups.

    Sets all 18 ``zmessaging.methodLevel`` slots **and** the legacy DSS-6
    Fortran ``MLVL`` global (via ``zset6_``), making it effective for both
    DSS-6 and DSS-7 files.  Prefer this over :attr:`GENERAL` when you want a
    single level for everything.  This is what :func:`get_dss_logger` returns
    when called with no argument.
    """

    GENERAL = 1
    """General DSS-7 operations not covered by a more specific group.

    Like :attr:`GLOBAL`, also fans out to all 18 method slots — but does
    **not** set the DSS-6 Fortran ``MLVL`` global.  Has no effect on DSS-6
    code paths (e.g. ``zopen6``).  Use :attr:`GLOBAL` instead when broad
    level control is needed.
    """

    GET = 2
    """Low-level record-get operations (``zget``)."""

    PUT = 3
    """Low-level record-put operations (``zput``)."""

    READ = 4
    """High-level read operations (``zread``)."""

    WRITE = 5
    """High-level write operations (``zwrite``)."""

    PERM = 6
    """Permanent-storage / housekeeping operations."""

    OPEN = 7
    """File open and close operations (``zopen`` / ``zclose``)."""

    CHECK = 8
    """Record existence checks (``zcheck``)."""

    LOCKING = 9
    """Multi-user file-locking operations."""

    TS_READ = 10
    """Time-series read operations (``ztsRetrieve``, ``ztsRetrieveReg``, …)."""

    TS_WRITE = 11
    """Time-series write operations (``ztsStore``, ``ztsStoreReg``, …)."""

    ALIAS = 12
    """Alias management (``zaliasAdd``, ``zaliasRemove``, …)."""

    COPY = 13
    """Record copy / duplicate operations."""

    UTILITY = 14
    """Miscellaneous utility functions."""

    CATALOG = 15
    """Catalog operations (``zcatalog``)."""

    FILE_CHECK = 16
    """File-integrity check operations."""

    JNI = 17
    """Java Native Interface bridge (not used from pure Python)."""


# ---------------------------------------------------------------------------
# Internal: Python logging → DSS level mapping tables
# ---------------------------------------------------------------------------

# Python logging integers → DSS Level.
# logging.CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10, NOTSET=0
_PYTHON_INT_TO_DSS: dict[int, Level] = {
    _logging.CRITICAL: Level.CRITICAL,
    _logging.ERROR:    Level.CRITICAL,
    _logging.WARNING:  Level.TERSE,
    _logging.INFO:     Level.GENERAL,
    _logging.DEBUG:    Level.USER_DIAG,
    _logging.NOTSET:   Level.GENERAL,
}

# Python logging name strings → DSS Level (case-insensitive keys stored lower).
_PYTHON_NAME_TO_DSS: dict[str, Level] = {
    "debug":    Level.USER_DIAG,
    "info":     Level.GENERAL,
    "warning":  Level.TERSE,
    "warn":     Level.TERSE,
    "error":    Level.CRITICAL,
    "critical": Level.CRITICAL,
    "notset":   Level.GENERAL,
}


def _resolve_level(level: Union[Level, int, str]) -> Level:
    """Convert *level* to a :class:`Level` enum value.

    Resolution order
    ~~~~~~~~~~~~~~~~
    1. :class:`Level` instance → returned as-is.
    2. ``int`` in 0–6 → treated as a DSS level integer.
    3. ``int`` in ``{0, 10, 20, 30, 40, 50}`` → mapped from Python logging
       integers via :data:`_PYTHON_INT_TO_DSS`.
    4. ``str`` matching a :class:`Level` member name (case-insensitive) → DSS
       level name (e.g. ``"TERSE"``, ``"user_diag"``).
    5. ``str`` matching a Python logging name (case-insensitive) → mapped via
       :data:`_PYTHON_NAME_TO_DSS` (e.g. ``"WARNING"``, ``"debug"``).

    Raises
    ------
    ValueError
        If *level* cannot be resolved.
    TypeError
        If *level* is not a :class:`Level`, ``int``, or ``str``.
    """
    if isinstance(level, Level):
        return level

    if isinstance(level, int):
        # DSS range takes priority (0-6) to avoid ambiguity with logging.NOTSET=0
        if 0 <= level <= 6:
            return Level(level)
        if level in _PYTHON_INT_TO_DSS:
            return _PYTHON_INT_TO_DSS[level]
        raise ValueError(
            f"Integer level {level!r} is not a valid DSS level (0-6) "
            f"or a recognised Python logging integer (0, 10, 20, 30, 40, 50)."
        )

    if isinstance(level, str):
        key = level.upper()
        # Try DSS level names first (NONE, CRITICAL, TERSE, GENERAL, …)
        try:
            return Level[key]
        except KeyError:
            pass
        # Fall back to Python logging names (DEBUG, INFO, WARNING, …)
        dss = _PYTHON_NAME_TO_DSS.get(level.lower())
        if dss is not None:
            return dss
        raise ValueError(
            f"Unknown level string {level!r}.  "
            f"Valid DSS names: {[m.name for m in Level]}.  "
            f"Valid Python logging names: {list(_PYTHON_NAME_TO_DSS)}."
        )

    raise TypeError(
        f"level must be a Level, int, or str; got {type(level).__name__!r}."
    )


def _resolve_method(method: Union[Method, int, str, None]) -> Method:
    """Convert *method* to a :class:`Method` enum value.

    Accepts a :class:`Method` enum member, an integer ID (0–17), or a
    case-insensitive string name (e.g. ``"locking"``, ``"TS_READ"``).
    ``None`` is treated as :attr:`Method.GLOBAL`.

    Raises
    ------
    ValueError
        If *method* cannot be resolved.
    TypeError
        If *method* is not a :class:`Method`, ``int``, ``str``, or ``None``.
    """
    if method is None:
        return Method.GLOBAL
    if isinstance(method, Method):
        return method
    if isinstance(method, int):
        try:
            return Method(method)
        except ValueError:
            raise ValueError(
                f"Integer method {method!r} is not a valid DSS method ID (0–17)."
            )
    if isinstance(method, str):
        try:
            return Method[method.upper()]
        except KeyError:
            raise ValueError(
                f"Unknown method string {method!r}.  "
                f"Valid names: {[m.name for m in Method]}."
            )
    raise TypeError(
        f"method must be a Method, int, str, or None; got {type(method).__name__!r}."
    )


# ---------------------------------------------------------------------------
# DssLogger
# ---------------------------------------------------------------------------

class DssLogger:
    """Controls the verbosity of one DSS C library method group.

    Do not instantiate directly — use :func:`get_dss_logger` instead, which
    returns a cached instance per method (the same pattern as
    :func:`logging.getLogger`).

    Parameters
    ----------
    method:
        The :class:`Method` group this logger controls.
    """

    __slots__ = ("_method",)

    def __init__(self, method: Method) -> None:
        self._method = method

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def method(self) -> Method:
        """The :class:`Method` group this logger controls (read-only)."""
        return self._method

    @property
    def level(self) -> Level:
        """The current :class:`Level` for this method group.

        Reads directly from the C library's internal ``zmessaging.methodLevel``
        array via ``zgetMessageLevel``, so it always reflects the true state —
        including propagation from :attr:`~Method.GLOBAL` or
        :attr:`~Method.GENERAL` set_level calls, which the C library
        fans out to all 18 method slots automatically.
        """
        return Level(_getMessageLevel(int(self._method)))

    def set_level(self, level: Union[Level, int, str]) -> None:
        """Set the verbosity level for this method group.

        Accepts any of the following forms:

        * A :class:`Level` enum member (``Level.GENERAL``).
        * A DSS integer 0–6 (``3``).
        * A Python :mod:`logging` integer (``logging.WARNING`` → ``Level.TERSE``).
        * A DSS level name string, case-insensitive
          (``"TERSE"``, ``"user_diag"``).
        * A Python :mod:`logging` name string, case-insensitive
          (``"WARNING"`` → ``Level.TERSE``, ``"debug"`` → ``Level.USER_DIAG``).

        The Python logging integer / name mapping is:

        ==================  =====  ==============
        Python              int    DSS Level
        ==================  =====  ==============
        ``logging.CRITICAL``  50   ``CRITICAL``
        ``logging.ERROR``     40   ``CRITICAL``
        ``logging.WARNING``   30   ``TERSE``
        ``logging.INFO``      20   ``GENERAL``
        ``logging.DEBUG``     10   ``USER_DIAG``
        ``logging.NOTSET``     0   ``GENERAL``
        ==================  =====  ==============

        Parameters
        ----------
        level:
            New verbosity level.

        Raises
        ------
        ValueError
            If *level* cannot be resolved to a :class:`Level`.
        TypeError
            If *level* has an unexpected type.
        """
        resolved = _resolve_level(level)
        _setMessageLevel(int(self._method), int(resolved))

    @contextmanager
    def suppress(self):
        """Context manager that silences all output from this method group.

        On exit — even if an exception is raised — the level is restored to
        whatever it was before entering the block.

        To silence output permanently (not just for a block), set
        :attr:`~Level.NONE` directly::

            get_dss_logger().set_level(Level.NONE)

        Example
        -------
        ::

            # Temporary — previous level restored after the block
            with get_dss_logger().suppress():
                fid.read_ts(pathname)   # no DSS messages printed
        """
        old = self.level
        try:
            self.set_level(Level.NONE)
            yield
        finally:
            self.set_level(old)

    @contextmanager
    def at_level(self, level: Union[Level, int, str]):
        """Context manager that temporarily sets this group's level.

        On exit — even if an exception is raised — the previous level is
        restored.

        Parameters
        ----------
        level:
            Temporary level; accepts the same forms as :meth:`set_level`.

        Example
        -------
        ::

            with get_dss_logger(Method.LOCKING).at_level(Level.CRITICAL):
                fid.read_ts(pathname)   # locking limited to errors only
            # locking level restored to what it was before
        """
        old = self.level
        try:
            self.set_level(level)
            yield
        finally:
            self.set_level(old)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"DssLogger({self._method.name}, level={self.level.name})"


# ---------------------------------------------------------------------------
# Logger cache and factory
# ---------------------------------------------------------------------------

_loggers: dict[Method, DssLogger] = {}


def get_dss_logger(
    method: Union[Method, int, str, None] = None,
) -> DssLogger:
    """Return the :class:`DssLogger` for the given DSS method group.

    This is the primary entry point for this module, analogous to
    :func:`logging.getLogger`.  The same :class:`DssLogger` instance is
    returned for the same *method* on every call (instances are cached).

    Parameters
    ----------
    method:
        The DSS method group to retrieve.  Accepts:

        * ``None`` or ``"global"`` → :attr:`Method.GLOBAL` (controls all groups).
        * A :class:`Method` enum member.
        * An integer method ID 0–17.
        * A case-insensitive string name matching a :class:`Method` member
          (e.g. ``"locking"``, ``"TS_READ"``, ``"open"``).

    Returns
    -------
    DssLogger
        Cached logger instance for the requested method group.

    Raises
    ------
    ValueError
        If *method* is a string or integer that cannot be resolved.
    TypeError
        If *method* has an unexpected type.

    Examples
    --------
    ::

        from pydsstools.heclib.logging import get_dss_logger, Level, Method
        import logging

        # Global logger (controls all method groups at once)
        get_dss_logger().set_level(Level.GENERAL)
        get_dss_logger(None).set_level(Level.GENERAL)   # same thing

        # By Method enum
        get_dss_logger(Method.LOCKING).set_level(Level.CRITICAL)

        # By integer ID
        get_dss_logger(9).set_level(Level.CRITICAL)

        # By name string (case-insensitive)
        get_dss_logger("locking").set_level(Level.CRITICAL)

        # Accept Python logging integers
        get_dss_logger().set_level(logging.WARNING)     # → Level.TERSE

        # Accept Python logging name strings
        get_dss_logger("ts_write").set_level("debug")   # → Level.USER_DIAG

        # Query
        logger = get_dss_logger(Method.TS_READ)
        print(logger)          # DssLogger(TS_READ, level=TERSE)
        print(logger.level)    # Level.TERSE

        # Context managers
        with get_dss_logger().suppress():
            dss.read(...)

        with get_dss_logger(Method.LOCKING).at_level(Level.CRITICAL):
            dss.read(...)
    """
    key = _resolve_method(method)
    if key not in _loggers:
        _loggers[key] = DssLogger(key)
    return _loggers[key]


# ---------------------------------------------------------------------------
# Library default
# ---------------------------------------------------------------------------

# Set DSS C library messaging to TERSE at import time via GLOBAL.
#
# Why GLOBAL: it writes all 18 zmessaging.methodLevel slots AND sets the
# DSS-6 Fortran MLVL global (via zset6_), making it effective for both
# DSS-6 and DSS-7 files.  The C library's own zresetMessageLevel() (called
# inside zinit()) writes the array directly and does not touch the Fortran
# layer, so this call is also the first proper initialisation of that layer.
#
# Why TERSE: the C library default (GENERAL) prints a line for every open,
# close, and write.  TERSE limits output to open/close events and errors,
# which is a quieter and more appropriate default for a Python library.
# Users who need more detail call get_dss_logger().set_level(Level.GENERAL).
get_dss_logger().set_level(Level.TERSE)
