"""HEC-DSS Time Handling

This module provides datetime conversion and manipulation for HEC-DSS (Hydrologic
Engineering Center - Data Storage System) files. It handles conversion between
various datetime string formats and the internal Julian day representation.

Classes
-------
HecTime : Main datetime handling class
    Stores time as julian days + seconds since midnight
    Supports multiple date/time string formats
    Provides arithmetic operations and conversions

Constants
---------
SECONDS_PER_MINUTE : int = 60
SECONDS_PER_HOUR : int = 3600
SECONDS_PER_DAY : int = 86400

Notes
-----
Julian day is defined as days since December 31, 1899.
This is the standard used by HEC-DSS for time representation.

See Also
--------
datetime : Python standard library datetime module
dateutil.parser : Third-party parsing library used for fallback

Examples
--------
Basic usage:

>>> from pydsstools.core import HecTime
>>> ht = HecTime("01Jan2000:1200")
>>> ht.date()
'01Jan2000'
>>> ht.time()
'12:00:00'
>>> ht.julian()
36526

Arithmetic operations:

>>> ht.add_hours(6)
>>> ht.time()
'18:00:00'

Format conversion:

>>> ht.text(format="%Y-%m-%d %H:%M")
'2000-01-01 18:00'
"""

# Regex patterns for parsing datetime string

__AMPM = r'(?:[AP]\.?M\.?|[AP])'

# ISO/XML format: 'YYYY-MM-DDThh:mm:ss[Z|+hh:mm]' or with space
__ISO = re.compile(
    r'^\s*(?P<date>-?\d{4,}-\d{2}-\d{2})[T ](?P<time>\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)\s*$',
    re.I
)

# Grid format: 'DATE:HHMM' or 'DATE:HHMMSS' - exactly one ':' in whole string
__GRID = re.compile(
    r'^\s*(?P<date>.+?)\s*:\s*(?P<time>\d{3,4}(?:\d{2})?)\s*[;,.]*\s*$',
    re.I
)

# Trailing time with colons: 'hh:mm[:ss][ AM/PM]'
# Requires non-digit before time to avoid mis-parsing "...1985:01:00" as "5:01:00"
__COLON_TIME = re.compile(
    rf'(?<!\d)(?P<time>\d{{1,2}}:\d{{2}}(?::\d{{2}})?(?:\s*{__AMPM})?)\s*[;,.]*\s*$',
    re.I
)

# Plain time: 'hhmm[ AM/PM]' or 'hhmmss[ AM/PM]'
__PLAIN_TIME = re.compile(
    rf'(?<!\d)(?P<time>\d{{3,4}}(?:\d{{2}})?(?:\s*{__AMPM})?)\s*[;,.]*\s*$',
    re.I
)

# ============================================================================
# Constants
# ============================================================================

# Time conversion constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400

# Valid granularity values (in seconds)
VALID_GRANULARITIES = (1, SECONDS_PER_MINUTE, SECONDS_PER_HOUR, SECONDS_PER_DAY)


# ============================================================================
# HecTime Class
# ============================================================================

cdef class HecTime:
    """HEC-DSS datetime handling class.

    This class provides datetime conversion and manipulation for HEC-DSS files.
    Time is stored internally as:
    - julian: Days since December 31, 1899
    - seconds: Seconds since midnight (0-86400)

    Parameters
    ----------
    date_time : str, datetime, HecTime, int, or None
        Input datetime in various formats:
        - str: Various date/time string formats (see split_datetime)
        - datetime: Python datetime object
        - HecTime: Clone another HecTime object
        - int: Timestep value (requires julian_base parameter)
        - None: Creates undefined time
    granularity : int, optional
        Time granularity in seconds. Must be 1, 60, 3600, or 86400.
        Default is 60 (minute precision).
    midnight_as_2400 : bool, optional
        If True, midnight is represented as 24:00 of previous day.
        If False, midnight is represented as 00:00 of current day.
        Default is False.
    date_style : int, optional
        Date formatting style code (see _date_style_codes()).
        Default is 2 (e.g., "2 June 1985").
    time_style : int, optional
        Time formatting style code 0-2, (see _time_style_codes()).
        0: "0830", 1: "08:30", 2: "08:30:00"
        Default is 2.
    julian_base : int or str, optional
        Base julian day for int timestep conversion.
        Can be julian day number or date string.
        Only used when date_time is int.

    Attributes
    ----------
    _julian : int
        Julian day number (days since Dec 31, 1899)
    _seconds_since_midnight : int
        Seconds since midnight (0-86400)
    _granularity : int
        Time precision in seconds
    _midnight_as_2400 : bool
        Midnight representation flag
    _date_style : int
        Date formatting style
    _time_style : int
        Time formatting style

    Raises
    ------
    ValueError
        If input datetime cannot be parsed
        If granularity is not valid
    TypeError
        If date_time type is not supported

    Examples
    --------
    Create from string:

    >>> ht = HecTime("01Jan2000:1200")
    >>> print(ht.date(), ht.time())
    01Jan2000 12:00:00

    Create from datetime:

    >>> from datetime import datetime
    >>> dt = datetime(2000, 1, 1, 12, 0)
    >>> ht = HecTime(dt)

    Create from timesteps:

    >>> ht = HecTime(100, granularity=60, julian_base="01Jan2000")

    Clone another HecTime:

    >>> ht2 = HecTime(ht)

    Undefined time:

    >>> ht_undef = HecTime(None)
    >>> ht_undef.is_undefined()
    True

    Notes
    -----
    - All datetime strings are parsed flexibly using regex and dateutil
    - Julian day 0 = December 31, 1899
    - Seconds can be 86400 when midnight_as_2400 is True
    - UNDEFINED_TIME constant represents invalid/undefined time
    """

    cdef:
        int _julian
        int _seconds_since_midnight
        int _granularity
        bint _midnight_as_2400
        int _date_style
        int _time_style

    def __init__(self, *arg, **kwargs):
        cdef:
            str datetime_str
            str date_str, time_str
            object julian_base
            int granularity
            object jul_sec

        date_time = None
        if len(arg) != 0:
            date_time = arg[0]

        # Extract optional parameters
        granularity = kwargs.pop("granularity", SECONDS_PER_MINUTE)
        self._midnight_as_2400 = kwargs.pop("midnight_as_2400", False)
        self._date_style = kwargs.pop("date_style", 2)
        self._time_style = kwargs.pop("time_style", 2)

        # Validate and set granularity
        if granularity in VALID_GRANULARITIES:
            self._granularity = granularity
        else:
            logger.warning(
                f"Expected granularity to be one of {VALID_GRANULARITIES}, "
                f"but got {granularity}"
            )
            logger.warning("Using default granularity of 60 seconds")
            self._granularity = SECONDS_PER_MINUTE

        # Handle different input types
        if date_time is None:
            self._julian = UNDEFINED_TIME
            self._seconds_since_midnight = UNDEFINED_TIME

        elif isinstance(date_time, str):
            date_str, time_str = self.split_datetime(date_time)

            # Ensure time string is present
            if not time_str:
                time_str = "0000"

            # Format for C API (requires colon between date and time)
            datetime_str = f"{date_str}:{time_str}"

        elif isinstance(date_time, datetime):
            datetime_str = date_time.strftime("%d%b%Y:%H:%M:%S")

        elif isinstance(date_time, HecTime):
            # Clone another HecTime object
            self._julian = date_time.julian()
            self._seconds_since_midnight = date_time.seconds_since_midnight()
            self._granularity = date_time.granularity()
            self._midnight_as_2400 = date_time.midnight_as_2400()
            self._date_style = date_time.date_style()
            self._time_style = date_time.time_style()

        elif isinstance(date_time, int):
            # Convert from timestep value
            julian_base = kwargs.pop("julian_base", 0)
            jul_sec = HecTime._value_to_julian_seconds2(
                date_time, granularity, julian_base
            )
            self._julian = jul_sec[0]
            self._seconds_since_midnight = jul_sec[1]

        else:
            raise TypeError(
                f"Expected datetime, string, HecTime, int, or None, "
                f"but received {type(date_time).__name__}"
            )

        # Parse datetime string if we have one
        if isinstance(date_time, (datetime, str)):
            try:
                jul_sec = HecTime._datetime_to_julian_seconds(datetime_str)
            except Exception as e:
                raise ValueError(
                    f"Error parsing datetime '{date_time}': {e}"
                ) from e

            self._julian = jul_sec[0]
            self._seconds_since_midnight = jul_sec[1]

        # Apply midnight representation preference
        self.set_midnight_as_2400(self._midnight_as_2400)

    def value(self, none_as_undefined=False):
        """Get timestep value.

        Converts julian day and seconds to a timestep value based on
        the granularity setting.

        Parameters
        ----------
        none_as_undefined : bool, optional
            If True, return None for undefined time.
            If False, return UNDEFINED_TIME constant.
            Default is False.

        Returns
        -------
        int or None
            Timestep value, or None/UNDEFINED_TIME if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:0000", granularity=60)
        >>> ht.value()
        52704000

        >>> ht_undef = HecTime(None)
        >>> ht_undef.value(none_as_undefined=True)
        None

        Notes
        -----
        The timestep value is calculated as:
        value = julian * (86400/granularity) + seconds/granularity
        """
        cdef:
            int days
            int seconds
            int granularity
            int increments_in_day
            int increments_in_sec
            int value

        if self.is_undefined():
            return None if none_as_undefined else UNDEFINED_TIME

        days = self.julian()
        seconds = self.seconds_since_midnight()
        granularity = self.granularity()

        increments_in_day = <int>(SECONDS_PER_DAY / granularity)
        increments_in_sec = <int>(seconds / granularity)
        # TODO: value() always returns absolute minutes from the epoch (Dec 31 1899),
        # completely ignoring self._julian_base.  _value_to_julian_seconds2 uses
        # julian_base to convert a relative int offset back to an absolute julian,
        # so the two are asymmetric: construction from int(+base) → absolute, but
        # value() never subtracts base to restore the original relative offset.
        # For full round-trip support with non-epoch bases, value() should subtract
        # self._julian_base from days before computing the result.
        value = days * increments_in_day + increments_in_sec
        return value

    def text(self, format=None):
        """Get formatted datetime string.

        Parameters
        ----------
        format : str, optional
            strftime format string. If None, uses DSS format "DATE:TIME".
            Default is None.

        Returns
        -------
        str or None
            Formatted datetime string, or None if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1200")
        >>> ht.text()
        '01Jan2000:12:00:00'

        >>> ht.text(format="%Y-%m-%d %H:%M")
        '2000-01-01 12:00'

        >>> ht.text(format="%B %d, %Y at %I:%M %p")
        'January 01, 2000 at 12:00 PM'
        """
        if self.is_undefined():
            return None

        if format is None:
            return self.date() + ":" + self.time()

        return self.datetime().strftime(format)

    def julian(self):
        """Get Julian day number.

        Returns
        -------
        int
            Days since December 31, 1899, or UNDEFINED_TIME if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:0000")
        >>> ht.julian()
        36526

        Notes
        -----
        Julian day 0 = December 31, 1899
        This is the standard used by HEC-DSS
        """
        return self._julian

    def seconds_since_midnight(self):
        """Get seconds since midnight.

        Returns
        -------
        int
            Seconds since midnight (0-86400), or UNDEFINED_TIME if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1230")
        >>> ht.seconds_since_midnight()
        45000

        Notes
        -----
        - Range is 0-86400 (not 0-86399)
        - Value can be 86400 when midnight_as_2400 is True
        - Represents 24:00 of previous day, not 00:00 of current day
        """
        return self._seconds_since_midnight

    def granularity(self):
        """Get time granularity in seconds.

        Returns
        -------
        int
            Granularity in seconds (1, 60, 3600, or 86400)

        Examples
        --------
        >>> ht = HecTime("01Jan2000", granularity=3600)
        >>> ht.granularity()
        3600
        """
        return self._granularity

    def date_style(self):
        """Get date formatting style code.

        Returns
        -------
        int
            Date style code (see _date_style_codes())

        Examples
        --------
        >>> ht = HecTime("01Jan2000", date_style=4)
        >>> ht.date_style()
        4
        """
        return self._date_style

    def time_style(self):
        """Get time formatting style code.

        Returns
        -------
        int
            Time style code (0-3)
            0: "0830", 1: "08:30", 2: "08:30:00"

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1230", time_style=1)
        >>> ht.time_style()
        1
        """
        return self._time_style

    def midnight_as_2400(self):
        """Get midnight representation flag.

        Returns
        -------
        bool
            True if midnight is 24:00 of previous day,
            False if midnight is 00:00 of current day

        Examples
        --------
        >>> ht = HecTime("01Jan2000:0000", midnight_as_2400=True)
        >>> ht.midnight_as_2400()
        True
        >>> ht.date()
        '31Dec1999'
        >>> ht.time()
        '24:00:00'
        """
        return self._midnight_as_2400

    def set_midnight_as_2400(self, flag=True):
        """Set midnight representation mode.

        Parameters
        ----------
        flag : bool, optional
            If True, represent midnight as 24:00 of previous day.
            If False, represent midnight as 00:00 of current day.
            Default is True.

        Examples
        --------
        >>> ht = HecTime("01Jan2000:0000")
        >>> ht.set_midnight_as_2400(True)
        >>> print(ht.date(), ht.time())
        31Dec1999 24:00:00

        >>> ht.set_midnight_as_2400(False)
        >>> print(ht.date(), ht.time())
        01Jan2000 00:00:00

        Notes
        -----
        This adjusts the internal julian day and seconds to maintain
        the same absolute time while changing representation.
        """
        self._midnight_as_2400 = flag

        if not self.is_undefined():
            if flag:
                # Convert 00:00 to 24:00 of previous day
                if self.seconds_since_midnight() == 0:
                    self._julian -= 1
                    self._seconds_since_midnight = SECONDS_PER_DAY
            else:
                # Convert 24:00 to 00:00 of next day
                if self.seconds_since_midnight() == SECONDS_PER_DAY:
                    self._julian += 1
                    self._seconds_since_midnight = 0

    def is_undefined(self):
        """Check if time is undefined.

        Returns
        -------
        bool
            True if time is undefined, False otherwise

        Examples
        --------
        >>> ht = HecTime(None)
        >>> ht.is_undefined()
        True

        >>> ht = HecTime("01Jan2000")
        >>> ht.is_undefined()
        False
        """
        return (self._julian == UNDEFINED_TIME or
                self._seconds_since_midnight == UNDEFINED_TIME)

    def date(self, date_style=None):
        """Get formatted date string.

        Parameters
        ----------
        date_style : int, optional
            Date formatting style code (see _date_style_codes()).
            If None, uses instance date_style.
            Default is None.

        Returns
        -------
        str
            Formatted date string, or "UNDEFINED" if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1200")
        >>> ht.date()
        '01Jan2000'

        >>> ht.date(date_style=0)
        'January 1, 2000'

        >>> ht.date(date_style=-13)
        '2000-01-01'
        """
        if self.is_undefined():
            return "UNDEFINED"

        if date_style is None:
            date_style = self.date_style()

        return HecTime._julian_to_date(self.julian(), date_style)

    def time(self, time_style=None):
        """Get formatted time string.

        Parameters
        ----------
        time_style : int, optional
            Time formatting style code (0-3).
            0: "0830", 1: "08:30", 2: "08:30:00"
            If None, uses instance time_style.
            Default is None.

        Returns
        -------
        str
            Formatted time string, or "UNDEFINED" if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1230")
        >>> ht.time()
        '12:30:00'

        >>> ht.time(time_style=0)
        '1230'

        >>> ht.time(time_style=1)
        '12:30'
        """
        if self.is_undefined():
            return "UNDEFINED"

        if time_style is None:
            time_style = self.time_style()

        return HecTime._seconds_to_time(
            self.seconds_since_midnight(),
            time_style_code=time_style
        )

    def datetime(self):
        """Get Python datetime object.

        Returns
        -------
        datetime or None
            Python datetime object, or None if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1230")
        >>> ht.datetime()
        datetime.datetime(2000, 1, 1, 12, 30)

        Notes
        -----
        If midnight_as_2400 is True, automatically converts to 00:00
        representation before creating datetime object.
        """
        if self.is_undefined():
            return None

        htime = self
        if self.midnight_as_2400():
            # Convert 24:00 to 00:00 for datetime object
            htime = self.clone()
            htime.set_midnight_as_2400(False)

        # Format: 01Jun2025
        date = htime.date(104)
        # Format: 10:30:00
        time = htime.time(2)
        return datetime.strptime(f"{date} {time}", "%d%b%Y %H:%M:%S")

    def second(self):
        """Get second component (0-59).

        Returns
        -------
        int or None
            Second of minute (0-59), or None if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:34:56")
        >>> ht.second()
        56

        Notes
        -----
        Optimized to calculate directly from seconds without string parsing.
        """
        if self.is_undefined():
            return None
        return self._seconds_since_midnight % SECONDS_PER_MINUTE

    def minute(self):
        """Get minute component (0-59).

        Returns
        -------
        int or None
            Minute of hour (0-59), or None if undefined

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:34:56")
        >>> ht.minute()
        34

        Notes
        -----
        Optimized to calculate directly from seconds without string parsing.
        """
        if self.is_undefined():
            return None
        return (self._seconds_since_midnight // SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE

    def hour(self):
        """Get hour component (0-23).

        Returns
        -------
        int or None
            Hour of day (0-23), or None if undefined
            Note: Can be 24 if midnight_as_2400 is True

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:34:56")
        >>> ht.hour()
        12

        >>> ht = HecTime("01Jan2000:0000", midnight_as_2400=True)
        >>> ht.hour()
        24

        Notes
        -----
        Optimized to calculate directly from seconds without string parsing.
        """
        if self.is_undefined():
            return None
        return self._seconds_since_midnight // SECONDS_PER_HOUR

    def day(self):
        """Get day of month (1-31).

        Returns
        -------
        int or None
            Day of month, or None if undefined

        Examples
        --------
        >>> ht = HecTime("15Jan2000:1200")
        >>> ht.day()
        15
        """
        if self.is_undefined():
            return None

        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[2]
        return None

    def month(self):
        """Get month (1-12).

        Returns
        -------
        int or None
            Month of year (1-12), or None if undefined

        Examples
        --------
        >>> ht = HecTime("15Jan2000:1200")
        >>> ht.month()
        1
        """
        if self.is_undefined():
            return None

        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[1]
        return None

    def year(self):
        """Get year.

        Returns
        -------
        int or None
            Four-digit year, or None if undefined

        Examples
        --------
        >>> ht = HecTime("15Jan2000:1200")
        >>> ht.year()
        2000
        """
        if self.is_undefined():
            return None

        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[0]
        return None

    def add_seconds(self, int count):
        """Add seconds to this time.

        Parameters
        ----------
        count : int
            Number of seconds to add (can be negative)

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:00:00")
        >>> ht.add_seconds(90)
        >>> ht.time()
        '12:01:30'

        See Also
        --------
        add_minutes, add_hours, add_days, add_time
        """
        self.add_time(1, count)

    def add_minutes(self, int count):
        """Add minutes to this time.

        Parameters
        ----------
        count : int
            Number of minutes to add (can be negative)

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:00:00")
        >>> ht.add_minutes(45)
        >>> ht.time()
        '12:45:00'

        See Also
        --------
        add_seconds, add_hours, add_days, add_time
        """
        self.add_time(SECONDS_PER_MINUTE, count)

    def add_hours(self, int count):
        """Add hours to this time.

        Parameters
        ----------
        count : int
            Number of hours to add (can be negative)

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:00:00")
        >>> ht.add_hours(6)
        >>> ht.time()
        '18:00:00'

        See Also
        --------
        add_seconds, add_minutes, add_days, add_time
        """
        self.add_time(SECONDS_PER_HOUR, count)

    def add_days(self, int count):
        """Add days to this time.

        Parameters
        ----------
        count : int
            Number of days to add (can be negative)

        Examples
        --------
        >>> ht = HecTime("01Jan2000:12:00")
        >>> ht.add_days(10)
        >>> ht.date()
        '11Jan2000'

        See Also
        --------
        add_seconds, add_minutes, add_hours, add_time
        """
        self.add_time(SECONDS_PER_DAY, count)

    def add_delta(self, rdelta):
        """Add a relativedelta to this time.

        Parameters
        ----------
        rdelta : dateutil.relativedelta.relativedelta
            Relative time delta to add

        Raises
        ------
        TypeError
            If rdelta is not a relativedelta instance

        Examples
        --------
        >>> from dateutil.relativedelta import relativedelta
        >>> ht = HecTime("01Jan2000:12:00")
        >>> ht.add_delta(relativedelta(months=2, days=5))
        >>> ht.date()
        '06Mar2000'

        Notes
        -----
        This method converts to datetime, adds the delta, then converts back.
        It's useful for complex date arithmetic (e.g., adding months/years).

        See Also
        --------
        add_seconds, add_minutes, add_hours, add_days
        """
        if not isinstance(rdelta, relativedelta):
            raise TypeError(
                f"Expected dateutils.relativedelta, "
                f"but received {type(rdelta).__name__}"
            )

        if self.is_undefined():
            return

        # Convert to datetime, add delta, convert back
        dt = self.datetime()
        dt += rdelta
        htime = HecTime(
            dt,
            granularity=self.granularity(),
            midnight_as_2400=self.midnight_as_2400(),
            date_style=self.date_style(),
            time_style=self.time_style(),
        )

        # Update internal state
        self._julian = htime.julian()
        self._seconds_since_midnight = htime.seconds_since_midnight()
        self._granularity = htime.granularity()
        self._date_style = htime.date_style()
        self._time_style = htime.time_style()
        self._midnight_as_2400 = htime.midnight_as_2400()

    def add_time(self, interval_seconds, periods=1):
        """Add time interval to this time.

        Parameters
        ----------
        interval_seconds : int
            Size of time interval in seconds
        periods : int, optional
            Number of intervals to add (can be negative).
            Default is 1.

        Examples
        --------
        >>> ht = HecTime("01Jan2000:00:00")
        >>> ht.add_time(3600, 5)  # Add 5 hours
        >>> ht.time()
        '05:00:00'

        >>> ht.add_time(86400, -2)  # Subtract 2 days
        >>> ht.date()
        '30Dec1999'

        Notes
        -----
        Automatically handles day/month/year rollovers.
        Normalizes time after addition.

        See Also
        --------
        add_seconds, add_minutes, add_hours, add_days
        """
        if self.is_undefined():
            return

        jul_sec = HecTime._increment_julian_date_time(
            self.julian(),
            self.seconds_since_midnight(),
            interval_seconds,
            periods
        )

        self._julian = jul_sec[0]
        self._seconds_since_midnight = jul_sec[1]
        self.normalize_time()

    def clone(self):
        """Create a copy of this HecTime object.

        Returns
        -------
        HecTime
            New HecTime object with same values

        Examples
        --------
        >>> ht1 = HecTime("01Jan2000:1200")
        >>> ht2 = ht1.clone()
        >>> ht2.add_hours(6)
        >>> ht1.time()  # Original unchanged
        '12:00:00'
        >>> ht2.time()  # Clone changed
        '18:00:00'
        """
        return HecTime(self)

    @staticmethod
    def _validate_date_part(date_str):
        """Validate that a string is a valid date (internal helper).

        Parameters
        ----------
        date_str : str
            Date string to validate

        Returns
        -------
        bool
            True if valid date, False otherwise

        Notes
        -----
        Used internally by split_datetime() to validate regex matches.
        Checks that dateutil can parse it as a date-only string.
        """
        try:
            dt = parser.parse(date_str)
        except Exception:
            logger.debug(f"Date validation failed for: '{date_str}'")
            return False

        # Check that parsed result has no time component
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
            logger.debug(f"Date '{date_str}' has non-zero time component")
            return False

        # Check for trailing zeros that dateutil accepts but shouldn't
        if date_str.endswith("0"):
            # Find last non-whitespace position
            j = len(date_str)
            for i, x in enumerate(reversed(date_str)):
                if not x.strip():
                    j = len(date_str) - i
                    _date = date_str[0:j].strip()

                    try:
                        _dt = parser.parse(_date)
                        if _dt == dt:
                            # Has meaningless trailing zeros
                            logger.debug(f"Date '{date_str}' has trailing zeros")
                            return False
                    except Exception:
                        pass

                    break

        return True

    @staticmethod
    def split_datetime(str s):
        """Split a datetime string into (date_str, time_str).

        This is a critical method that handles various datetime formats
        and separates them into date and time components.

        Parameters
        ----------
        s : str or None
            Input datetime string in various formats

        Returns
        -------
        tuple of (str, str)
            (date_str, time_str) components
            Returns ("", "") for None or "undefined"

        Raises
        ------
        ValueError
            If string cannot be parsed as a valid datetime

        Supported Formats
        -----------------
        1. ISO/XML: 'YYYY-MM-DDThh:mm:ss[Z|+hh:mm]' or with space
           Example: "2000-01-15T10:30:00"

        2. Grid style: 'DATE:HHMM' or 'DATE:HHMMSS'
           Example: "01JAN2000:1030", "JUN 1, 1985:010000"
           Note: Only if exactly one ':' in entire string

        3. Colon time: 'DATE hh:mm[:ss][ AM/PM]'
           Examples: "01JAN2000 10:30", "Jan 1, 2000 2:30 PM"

        4. Plain time: 'DATE hhmm[ AM/PM]'
           Examples: "01JAN2000 1030", "Jan 1, 2000 1430"

        5. Date only: 'DATE'
           Example: "01JAN2000", "January 1, 2000"
           Returns: (date, "")

        6. Special: "undefined" (case-insensitive)
           Returns: ("", "")

        Examples
        --------
        >>> HecTime.split_datetime("2000-01-15T10:30:00")
        ('2000-01-15', '10:30:00')

        >>> HecTime.split_datetime("01JAN2000:1030")
        ('01JAN2000', '1030')

        >>> HecTime.split_datetime("Jan 1, 2000 10:30 AM")
        ('Jan 1, 2000', '10:30 AM')

        >>> HecTime.split_datetime("01JAN2000")
        ('01JAN2000', '')

        >>> HecTime.split_datetime("undefined")
        ('', '')

        Notes
        -----
        The method tries multiple parsing strategies in order:
        1. Check for None or "undefined"
        2. Try dateutil parser for date-only detection
        3. Try specific regex patterns (ISO, Grid, Colon, Plain)
        4. Fall back to dateutil for complex formats
        5. Raise ValueError if all strategies fail

        Trailing punctuation (.,;:-) is stripped from date part.
        AM/PM indicators are preserved in time part.

        Performance: Optimized to try faster regex matches before
        falling back to slower dateutil parsing.
        """
        # Handle None and special cases
        if s is None:
            return ("", "")

        s_stripped = s.strip()
        if s_stripped.lower() == "undefined":
            logger.debug('Parsed as undefined ("", "")')
            return ("", "")

        # Try dateutil first for date-only detection
        success_with_dateutil = False
        dt = None

        try:
            dt = parser.parse(s_stripped)
            success_with_dateutil = True
        except Exception:
            logger.debug(
                f"Failed to parse '{s}' with dateutil; "
                "trying regex-based parsing"
            )

        # Handle date-only case from dateutil
        if success_with_dateutil and dt is not None:
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                logger.debug(f"Parsed via dateutil: '{s}' is date-only")

                # Clean trailing punctuation
                s_clean = s.strip()
                if s_clean and s_clean[-1] in (".", ",", "-", "_", ";", ":"):
                    s_clean = s_clean[0:-1].strip()

                # Check for all-zero time components that should be removed
                if s_clean.endswith("00"):
                    # Find where zeros start
                    j = len(s_clean)
                    for i, x in enumerate(reversed(s_clean)):
                        if x not in ("0", ":"):
                            j = len(s_clean) - i
                            _date_part = s_clean[0:j].strip()
                            _time_part = s_clean[j:]

                            if _date_part and _date_part[-1] in (".", ",", "-", "_", ";", ":"):
                                _date_part = _date_part[0:-1].strip()

                            # Verify the date part alone parses to same datetime
                            try:
                                _dt = parser.parse(_date_part)
                                if _dt == dt:
                                    logger.debug(
                                        f"Removed all-zero time suffix '{_time_part}' "
                                        f"from '{s}'"
                                    )
                                    s_clean = _date_part
                            except Exception:
                                pass

                            break

                result = (s_clean, "")
                logger.debug(f"Parsed as {result}")
                return result

        # Try regex patterns in order of specificity
        # 1) ISO/XML format
        m = __ISO.match(s_stripped)
        if m:
            result = (m.group('date'), m.group('time'))
            if HecTime._validate_date_part(result[0]):
                logger.debug(f"Parsed as ISO format: {result}")
                return result

        # 2) Grid format (exactly one colon in entire input)
        if s_stripped.count(':') == 1:
            m = __GRID.match(s_stripped)
            if m:
                date_part = m.group('date').rstrip(' ,;:.')
                time_part = m.group('time')
                result = (date_part, time_part)
                if HecTime._validate_date_part(result[0]):
                    logger.debug(f"Parsed as GRID format: {result}")
                    return result

        # 3) Trailing hh:mm[:ss][ AM/PM]
        m = __COLON_TIME.search(s_stripped)
        if m:
            start = m.start('time')
            date_part = s_stripped[:start].rstrip(' ,;:.')
            time_part = s_stripped[start:].strip().rstrip(' ,;')
            result = (date_part, time_part)
            if HecTime._validate_date_part(result[0]):
                logger.debug(f"Parsed as COLON_TIME format: {result}")
                return result

        # 4) Trailing hhmm[ AM/PM]
        m = __PLAIN_TIME.search(s_stripped)
        if m:
            start = m.start('time')
            date_part = s_stripped[:start].rstrip(' ,;:.')
            time_part = s_stripped[start:].strip().rstrip(' ,;')
            result = (date_part, time_part)
            if HecTime._validate_date_part(result[0]):
                logger.debug(f"Parsed as PLAIN_TIME format: {result}")
                return result

        # Fall back to dateutil if it succeeded earlier
        if success_with_dateutil and dt is not None:
            logger.info(f"Falling back to dateutil result: '{dt}'")
            return dt.strftime("%d%b%Y:%H%M%S").split(":")

        # All parsing strategies failed
        raise ValueError(f"Unable to parse datetime string '{s}'.")

    def __repr__(self):
        """Get string representation of HecTime object.

        Returns
        -------
        str
            String in format: HecTime(date time midnight-as-2400=flag)

        Examples
        --------
        >>> ht = HecTime("01Jan2000:1200")
        >>> repr(ht)
        'HecTime(01Jan2000 12:00:00 midnight-as-2400=False)'
        """
        return (
            f"{self.__class__.__name__}("
            f"{self.date()} {self.time()} "
            f"midnight-as-2400={self._midnight_as_2400})"
        )

    def normalize_time(self):
        """Normalize time to handle overflow/underflow.

        Adjusts julian day and seconds if seconds are outside 0-86400 range.
        This is called automatically after arithmetic operations.

        Examples
        --------
        >>> ht = HecTime("01Jan2000:2300")
        >>> ht._seconds_since_midnight = 90000  # > 86400
        >>> ht.normalize_time()
        >>> ht.date()
        '02Jan2000'
        >>> ht.seconds_since_midnight()
        3600

        Notes
        -----
        - Seconds > 86400: adds day, reduces seconds
        - Seconds < 0: subtracts day, increases seconds
        - Preserves midnight_as_2400 representation
        """
        if not self.is_undefined():
            jul_sec = HecTime._clean_time(
                self.julian(),
                self.seconds_since_midnight()
            )
            self._julian = jul_sec[0]
            self._seconds_since_midnight = jul_sec[1]
            self.set_midnight_as_2400(self.midnight_as_2400())

    # ==========================================================================
    # Static Helper Methods
    # ==========================================================================

    @staticmethod
    def _clean_time(int julian, int seconds):
        """Normalize julian day and seconds (internal helper).

        Parameters
        ----------
        julian : int
            Julian day number
        seconds : int
            Seconds (may be outside 0-86400 range)

        Returns
        -------
        tuple of (int, int)
            Normalized (julian, seconds)

        Examples
        --------
        >>> HecTime._clean_time(100, 90000)  # 90000 > 86400
        (101, 3600)

        >>> HecTime._clean_time(100, -3600)  # Negative seconds
        (99, 82800)

        Notes
        -----
        This is an internal helper method.
        Public code should use normalize_time() instead.
        """
        if seconds > SECONDS_PER_DAY:
            julian += 1
            seconds = seconds - SECONDS_PER_DAY
        elif seconds < 0:
            julian -= 1
            seconds = SECONDS_PER_DAY + seconds  # Note: seconds is negative

        return (julian, seconds)

    @staticmethod
    def _datetime_from_value(int time, int granularity, int julian_base=0):
        """Convert timestep value to date and time strings.

        Parameters
        ----------
        time : int
            Timestep value
        granularity : int
            Granularity in seconds (1 or 60 only)
        julian_base : int, optional
            Base julian day. Default is 0.

        Returns
        -------
        tuple of (bytes, bytes) or None
            (date_string, time_string) or None if error

        Raises
        ------
        ValueError
            If granularity is not 1 or 60

        Notes
        -----
        This calls the C function getDateAndTime.
        """
        cdef:
            char cdate[20]
            char ctime[15]
            int size_date = sizeof(cdate)
            int size_time = sizeof(ctime)
            int status

        if granularity not in (1, SECONDS_PER_MINUTE):
            raise ValueError(
                f'Granularity must be 1 or 60 seconds, but {granularity} provided'
            )

        status = getDateAndTime(
            time, granularity, julian_base,
            cdate, size_date, ctime, size_time
        )

        if status == nok:
            return None

        return (cdate, ctime)

    @staticmethod
    def _value_to_julian_seconds(int time, int granularity, int julian_base=0):
        """Convert timestep value to julian day and seconds.

        Parameters
        ----------
        time : int
            Timestep value
        granularity : int
            Granularity in seconds
        julian_base : int, optional
            Base julian day. Default is 0.

        Returns
        -------
        tuple of (int, int)
            (julian, seconds)

        Examples
        --------
        >>> HecTime._value_to_julian_seconds(1440, 60, 0)
        (1, 0)  # 1440 minutes = 1 day

        >>> HecTime._value_to_julian_seconds(100, 3600, 0)
        (4, 14400)  # 100 hours = 4 days + 4 hours
        """
        cdef:
            int julian
            int seconds
            int increments_in_day

        increments_in_day = <int>(SECONDS_PER_DAY / granularity)
        julian = <int>(time / increments_in_day)
        seconds = (time - julian * increments_in_day) * granularity
        julian += julian_base

        return (julian, seconds)

    @staticmethod
    def _value_to_julian_seconds2(int time, int granularity, object julian_basedate):
        """Convert timestep value to julian/seconds with flexible base date.

        Parameters
        ----------
        time : int
            Timestep value
        granularity : int
            Granularity in seconds
        julian_basedate : int or str
            Base julian day as integer, or date string to convert

        Returns
        -------
        tuple of (int, int)
            (julian, seconds)

        Raises
        ------
        ValueError
            If julian_basedate is invalid

        Examples
        --------
        >>> HecTime._value_to_julian_seconds2(100, 60, 0)
        (0, 6000)

        >>> HecTime._value_to_julian_seconds2(100, 60, "01Jan2000")
        (36526, 6000)
        """
        julian_base = julian_basedate

        if isinstance(julian_basedate, str):
            julian_base = HecTime._date_to_julian(julian_basedate)

        if not isinstance(julian_base, int):
            raise ValueError(
                f"Invalid julian base date ({julian_basedate}) provided"
            )

        return HecTime._value_to_julian_seconds(time, granularity, julian_base)

    @staticmethod
    def _datetime_to_julian_seconds(str std_datetime_str):
        """Convert datetime string to julian day and seconds.

        Parameters
        ----------
        std_datetime_str : str
            Datetime in format "DDMmmYYYY:HHMM" or "DDMmmYYYY:HH:MM:SS"
            Examples: "01DEC2016:0000", "01DEC2016:00:00", "01DEC2016:00:00:00"

        Returns
        -------
        tuple of (int, int) or None
            (julian_days, seconds) or None if empty/invalid

        Raises
        ------
        ValueError
            If datetime string cannot be parsed

        Notes
        -----
        - Date and time must be separated with colon
        - Calls C function spatialDateTime
        - "2400" returns 86400 seconds (next day midnight)
        - "0000" returns 0 seconds
        - Result is normalized via _clean_time

        Examples
        --------
        >>> HecTime._datetime_to_julian_seconds("01JAN2000:1200")
        (36526, 43200)

        >>> HecTime._datetime_to_julian_seconds("31DEC1999:2400")
        (36526, 0)  # Normalized to next day 00:00
        """
        cdef:
            char* cdatetime
            int days
            int seconds
            int status

        logger.debug(f"Converting '{std_datetime_str}' to (julian, seconds)")

        if not std_datetime_str:
            logger.debug('datetime is empty or None')
            return None

        cdatetime = std_datetime_str
        status = spatialDateTime(cdatetime, &days, &seconds)

        if status == nok:
            raise ValueError(
                f"Invalid datetime string '{std_datetime_str}' "
                "cannot be parsed to julian days and seconds"
            )

        days, seconds = HecTime._clean_time(days, seconds)

        return (days, seconds)

    @staticmethod
    def _dates_to_julian(date):
        """Convert various date formats to julian day (flexible wrapper).

        Parameters
        ----------
        date : int, str, tuple, list, datetime, or HecTime
            Date in various formats:
            - int: Julian day number (returned as-is)
            - str: Date string to parse
            - tuple/list: (year, month, day)
            - datetime: Python datetime object
            - HecTime: Extract julian from HecTime

        Returns
        -------
        int or None
            Julian day number, or None if invalid

        Examples
        --------
        >>> HecTime._dates_to_julian(36526)
        36526

        >>> HecTime._dates_to_julian("01Jan2000")
        36526

        >>> HecTime._dates_to_julian((2000, 1, 1))
        36526

        >>> from datetime import datetime
        >>> HecTime._dates_to_julian(datetime(2000, 1, 1))
        36526
        """
        cdef:
            int days
            str _date

        if isinstance(date, int):
            days = date
        elif isinstance(date, str):
            days = HecTime._date_to_julian(date)
        elif isinstance(date, (tuple, list)):
            days = HecTime._date_to_julian(*date)
        elif isinstance(date, datetime):
            _date = date.strftime("%d%b%Y")
            days = HecTime._date_to_julian(_date)
        elif isinstance(date, HecTime):
            days = date.julian()
        else:
            return None

        return days

    @staticmethod
    def _date_to_julian(*args):
        """Convert date to julian day number.

        Can be called with either a date string or year/month/day components.

        Parameters
        ----------
        *args : str or (int, int, int)
            Either:
            - Single str: date string (e.g., "01Jan2000")
            - Three ints: year, month, day (e.g., 2000, 1, 1)

        Returns
        -------
        int or None
            Julian day number, or None if undefined/invalid

        Raises
        ------
        TypeError
            If number of arguments is not 1 or 3

        Examples
        --------
        >>> HecTime._date_to_julian("01Jan2000")
        36526

        >>> HecTime._date_to_julian(2000, 1, 1)
        36526

        Notes
        -----
        Calls C functions dateToJulian or yearMonthDayToJulian.
        Returns None if C function returns UNDEFINED_TIME.
        """
        cdef:
            str date_str
            char* cdate
            int year
            int month
            int day
            int days

        if len(args) == 1:
            date_str = args[0]
            cdate = date_str
            days = dateToJulian(date_str)

        elif len(args) == 3:
            year = args[0]
            month = args[1]
            day = args[2]
            days = yearMonthDayToJulian(year, month, day)

        else:
            raise TypeError(
                f"Function takes either 1 (date) or 3 (year, month, day) "
                f"arguments, but {len(args)} were given"
            )

        if days == UNDEFINED_TIME:
            return None

        return days

    @staticmethod
    def _julian_to_date(int days, int date_style_code=4):
        """Convert julian day to formatted date string.

        Parameters
        ----------
        days : int
            Julian day number
        date_style_code : int, optional
            Date formatting style (see _date_style_codes()).
            Default is 4 ("02Jun1985").

        Returns
        -------
        bytes or None
            Formatted date string, or None if error

        Examples
        --------
        >>> HecTime._julian_to_date(36526, 4)
        b'01Jan2000'

        >>> HecTime._julian_to_date(36526, 0)
        b'January 1, 2000'

        Notes
        -----
        Calls C function julianToDate.
        See _date_style_codes() for all available style codes.
        """
        cdef:
            char cdate[20]
            int sz = sizeof(cdate)
            int status

        status = julianToDate(days, date_style_code, cdate, sz)

        if status == nok:
            return None

        return cdate

    @staticmethod
    def _julian_to_datetime(int days, int seconds, int date_style_code, int time_style_code):
        """Convert julian day/seconds to formatted date and time strings.

        Parameters
        ----------
        days : int
            Julian day number
        seconds : int
            Seconds since midnight
        date_style_code : int
            Date formatting style
        time_style_code : int
            Time formatting style (0-3)

        Returns
        -------
        tuple of (bytes, bytes)
            (date_string, time_string)

        Examples
        --------
        >>> HecTime._julian_to_datetime(36526, 43200, 4, 2)
        (b'01Jan2000', b'12:00:00')
        """
        cdef:
            str date_str
            str time_str

        date_str = HecTime._julian_to_date(days, date_style_code)
        time_str = HecTime._seconds_to_time(
            seconds,
            time_style_code=time_style_code
        )

        return (date_str, time_str)

    @staticmethod
    def _julian_to_dayofweek(int days):
        """Get day of week from julian day.

        Parameters
        ----------
        days : int
            Julian day number

        Returns
        -------
        int
            Day of week (1-7), where 1=Sunday, 7=Saturday

        Examples
        --------
        >>> HecTime._julian_to_dayofweek(36526)  # Jan 1, 2000
        7  # Saturday

        Notes
        -----
        Calls C function dayOfWeek.
        """
        cdef:
            int day

        day = dayOfWeek(days)
        return day

    @staticmethod
    def _julian_to_ymd(int days):
        """Convert julian day to year/month/day.

        Parameters
        ----------
        days : int
            Julian day number

        Returns
        -------
        tuple of (int, int, int) or None
            (year, month, day) or None if error

        Examples
        --------
        >>> HecTime._julian_to_ymd(36526)
        (2000, 1, 1)

        Notes
        -----
        Calls C function julianToYearMonthDay.
        """
        cdef:
            int year
            int month
            int day
            int status

        status = julianToYearMonthDay(days, &year, &month, &day)

        if status == nok:
            return None

        return (year, month, day)

    @staticmethod
    def _increment_julian_date_time(int jl_days, int jl_seconds,
                                     int interval_seconds, int number_periods):
        """Add time interval to julian day/seconds.

        Parameters
        ----------
        jl_days : int
            Starting julian day
        jl_seconds : int
            Starting seconds since midnight
        interval_seconds : int
            Size of interval in seconds
        number_periods : int
            Number of intervals to add (can be negative)

        Returns
        -------
        tuple of (int, int) or None
            (new_julian, new_seconds) or None if error

        Examples
        --------
        >>> HecTime._increment_julian_date_time(36526, 0, 3600, 25)
        (37527, 3600)  # Add 25 hours

        Notes
        -----
        Calls C function incrementTime.
        """
        cdef:
            int days
            int seconds
            int status

        status = incrementTime(
            interval_seconds, number_periods,
            jl_days, jl_seconds,
            &days, &seconds
        )

        if status == nok:
            return None

        return (days, seconds)

    @staticmethod
    def _minutes_to_hhmm(int minutes):
        """Convert minutes to HHMM string.

        Parameters
        ----------
        minutes : int
            Number of minutes

        Returns
        -------
        bytes
            Time in HHMM format (e.g., b"0130" for 90 minutes)

        Examples
        --------
        >>> HecTime._minutes_to_hhmm(90)
        b'0130'

        >>> HecTime._minutes_to_hhmm(750)
        b'1230'

        Notes
        -----
        Calls C function minutesToHourMin.
        """
        cdef:
            char hhmm[6]
            sz = sizeof(hhmm)

        minutesToHourMin(minutes, hhmm, sz)
        return hhmm

    @staticmethod
    def _seconds_to_time(int seconds, int milliseconds=0, int time_style_code=2):
        """Convert seconds to formatted time string.

        Parameters
        ----------
        seconds : int
            Seconds since midnight (0-86400)
        milliseconds : int, optional
            Milliseconds (0-999). Default is 0.
        time_style_code : int, optional
            Time formatting style (0-3).
            0: "0830", 1: "08:30", 2: "08:30:00"
            Default is 2.

        Returns
        -------
        bytes or None
            Formatted time string, or None if invalid style code

        Examples
        --------
        >>> HecTime._seconds_to_time(43200, 0, 2)
        b'12:00:00'

        >>> HecTime._seconds_to_time(43200, 0, 0)
        b'1200'

        >>> HecTime._seconds_to_time(86400, 0, 2)
        b'24:00:00'

        Notes
        -----
        Calls C function secondsToTimeString.
        Valid time_style_code values: 0, 1, 2, 3
        """
        cdef:
            char ctime[15]
            int sz = sizeof(ctime)

        if time_style_code in (0, 1, 2, 3):
            secondsToTimeString(seconds, milliseconds, time_style_code, ctime, sz)
            return ctime

        logger.warning(f"Unexpected time_style_code = {time_style_code} received")
        return None

    @staticmethod
    def _time_to_seconds(str time_str):
        """Convert time string to seconds.

        Parameters
        ----------
        time_str : str
            Time in various formats:
            - "0830" or "083045"
            - "08:30" or "08:30:43"
            - "08:30:43.5" (with fractional seconds)

        Returns
        -------
        float or None
            Seconds since midnight, or None if invalid

        Examples
        --------
        >>> HecTime._time_to_seconds("1230")
        45000.0

        >>> HecTime._time_to_seconds("12:30:45")
        45045.0

        >>> HecTime._time_to_seconds("12:30:45.5")
        45045.5

        Notes
        -----
        Calls C function timeStringToSecondsMills.
        Returns None if parsing fails.
        """
        cdef:
            float seconds
            char* ctime = time_str

        seconds = timeStringToSecondsMills(ctime)

        if seconds != nok:
            return seconds

        return None

    @staticmethod
    def _number_of_periods(int standard_interval_seconds,
                          int jul_start, int jul_start_seconds,
                          int jul_end, int jul_end_seconds):
        """Calculate number of periods between two times.

        Parameters
        ----------
        standard_interval_seconds : int
            Interval size in seconds
        jul_start : int
            Start julian day
        jul_start_seconds : int
            Start seconds since midnight
        jul_end : int
            End julian day
        jul_end_seconds : int
            End seconds since midnight

        Returns
        -------
        int or None
            Number of intervals, or None if error

        Examples
        --------
        >>> HecTime._number_of_periods(
        ...     3600,  # 1 hour intervals
        ...     36526, 0,  # Jan 1, 2000 00:00
        ...     36526, 10800  # Jan 1, 2000 03:00
        ... )
        3

        Notes
        -----
        Calls C function numberPeriods.
        """
        cdef:
            int count

        count = numberPeriods(
            standard_interval_seconds,
            jul_start, jul_start_seconds,
            jul_end, jul_end_seconds,
        )

        if count == nok:
            return None

        return count

    @staticmethod
    def _date_to_ymd(str date_str):
        """Convert date string to year/month/day.

        Parameters
        ----------
        date_str : str
            Date string (e.g., "01Jan2000")

        Returns
        -------
        tuple of (int, int, int) or None
            (year, month, day) or None if error

        Examples
        --------
        >>> HecTime._date_to_ymd("01Jan2000")
        (2000, 1, 1)

        >>> HecTime._date_to_ymd("15Jun1985")
        (1985, 6, 15)

        Notes
        -----
        Calls C function dateToYearMonthDay.
        """
        cdef:
            char* cdate = date_str
            int year
            int month
            int day
            int status

        status = dateToYearMonthDay(cdate, &year, &month, &day)

        if status == nok:
            return None

        return (year, month, day)

    @staticmethod
    def _add_century(int year):
        """Add century to two-digit year.

        Parameters
        ----------
        year : int
            Two-digit year (0-99)

        Returns
        -------
        int
            Four-digit year

        Examples
        --------
        >>> HecTime._add_century(85)
        1985

        >>> HecTime._add_century(25)
        2025

        Notes
        -----
        Calls C function addCentury.
        Uses standard windowing logic (typically 0-69 → 2000-2069, 70-99 → 1970-1999).
        """
        year = addCentury(year)
        return year

    @staticmethod
    def _is_leap(int year):
        """Check if year is a leap year.

        Parameters
        ----------
        year : int
            Four-digit year

        Returns
        -------
        int
            Non-zero if leap year, 0 if not

        Examples
        --------
        >>> HecTime._is_leap(2000)
        1

        >>> HecTime._is_leap(1900)
        0

        >>> HecTime._is_leap(2024)
        1

        Notes
        -----
        Calls C function isLeapYear.
        Leap year rules: divisible by 4, except centuries unless divisible by 400.
        """
        cdef:
            int status

        status = isLeapYear(year)
        return status

    @staticmethod
    def _date_style_codes():
        """Get all available date formatting style codes.

        Returns
        -------
        dict
            Mapping of style code (int) to example format (str)

        Examples
        --------
        >>> styles = HecTime._date_style_codes()
        >>> styles[0]
        'June 2, 1985'
        >>> styles[4]
        '02Jun1985'
        >>> styles[-13]
        '1985-06-02'

        Notes
        -----
        Positive codes 0-19: Various month/day/year formats
        Codes 100-119: Same as 0-19 but uppercase
        Negative codes: Numeric formats with slashes or dashes
        """
        styles = {
            0: "June 2, 1985",
            1: "Jun 2, 1985",
            2: "2 June 1985",
            3: "June 1985",
            4: "02Jun1985",
            5: "2Jun1985",
            6: "Jun1985",
            7: "02 Jun 1985",
            8: "2 Jun 1985",
            9: "Jun 1985",
            10: "June 2, 85",
            11: "Jun 2, 85",
            12: "2 June 85",
            13: "June 85",
            14: "02Jun85",
            15: "2Jun1985",
            16: "Jun85",
            17: "02 Jun 85",
            18: "2 Jun 85",
            19: "Jun 85",
        }

        # Add uppercase versions (100-119)
        codes = range(100, 120)
        styles.update(dict(zip(codes, [x.upper() for x in styles.values()])))

        # Add numeric formats
        styles.update({
            -1: "6/2/85",
            -2: "6-2-85",
            -11: "06/02/85",
            -12: "06-02-85",
            -13: "1985-06-02",
            -101: "6/2/1985",
            -102: "6-2-1985",
            -111: "06/02/1985",
            -112: "06-02-1985"
        })

        return styles

    @staticmethod
    def _time_style_codes():
        """Get all available time formatting style codes.

        Returns
        -------
        dict
            Mapping of style code (int) to example format (str)

        Examples
        --------
        >>> styles = HecTime._time_style_codes()
        >>> styles[0]
        '0830'
        >>> styles[1]
        '08:30'
        >>> styles[2]
        '08:30:00'

        Notes
        -----
        0: "HHMM" (e.g., "0830")
        1: "HH:MM" (e.g., "08:30")
        2: "HH:MM:SS" (e.g., "08:30:00")
        3: Reserved for fractional seconds (if supported)
        """
        styles = {
            0: "0830",
            1: "08:30",
            2: "08:30:00"
        }

        return styles
