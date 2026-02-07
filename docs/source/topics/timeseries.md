# Time Series

This guide covers reading, writing, and managing time-series records in
HEC-DSS files using **pydsstools**.

Time-series records store sequences of values measured or computed at
specific points in time. Common uses include streamflow hydrographs,
precipitation measurements, water level observations, and reservoir
operations data.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Regular Time Series** | Values recorded at a fixed interval (e.g., every hour, every day). The E-part of the pathname specifies the interval (e.g., `1HOUR`, `1DAY`). |
| **Irregular Time Series** | Values recorded at variable timestamps. The E-part uses an `IR-` prefix (e.g., `IR-DAY`, `IR-DECADE`). |
| **TimeSeriesContainer** | Write-side container. Holds pathname, interval, values, times, units, and type before writing to DSS. |
| **TimeSeriesStruct** | Read-side structure returned by the Cython layer. Wraps the C `zStructTimeSeries` and exposes values, times, and metadata. |
| **HecTime** | Datetime class for HEC-DSS. Stores time as julian days + seconds since midnight. Used for timestamps in irregular time series. |
| **UNDEFINED** | Sentinel float value representing missing data in DSS time-series cells. |
| **Granularity** | Time precision in seconds. Minute granularity (60) is the default. Second granularity (1) is available but requires care to avoid integer overflow. |
| **Window** | A date range tuple `(start, end)` for reading a subset of a time series. |

### Regular vs Irregular Time Series

```
Regular (1HOUR interval):
  01Jan2025 01:00  ->  10.0
  01Jan2025 02:00  ->  20.0    Fixed spacing, only start_time needed
  01Jan2025 03:00  ->  30.0

Irregular (IR-DAY):
  02Jul2010 12:00  ->   1.0
  05Jan2012 00:00  ->  20.0    Variable spacing, each value has a timestamp
  15Mar2014 02:00  ->  30.0
```

- **Regular** time series only need a `start_time` and `interval` — timestamps
  are computed automatically.
- **Irregular** time series need an explicit `times` array with one timestamp
  per value.

---

## Example 1 — Read a Regular Time Series

The most common use case. `read_ts()` returns a `TimeSeriesStruct` with
values and times.

```python
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR//"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(pathname)

    print("Type:", ts.dtype)             # "Regular TimeSeries"
    print("Count:", ts.count)            # Number of values
    print("Units:", ts.data_units)       # e.g., "cfs"
    print("Data type:", ts.data_type)    # e.g., "INST-VAL"
    print("Start:", ts.start_time)       # HecTime object
    print("End:", ts.end_time)           # HecTime object

    # Values as a NumPy array
    values = ts.values
    print("Values:", values)

    # Times as HecTime generator
    for t in ts.times:
        print(t.datetime(), "->", end=" ")
```

**TimeSeriesStruct properties:**

| Property | Type | Description |
|----------|------|-------------|
| `values` | ndarray | NumPy array of float values |
| `times` | generator of HecTime | Yields one HecTime per data point |
| `count` | int | Number of data points |
| `dtype` | str | `"Regular TimeSeries"` or `"Irregular TimeSeries"` |
| `data_units` | str | Units string (e.g., `"cfs"`, `"ft"`) |
| `data_type` | str | Type string (e.g., `"INST-VAL"`, `"PER-AVER"`) |
| `start_time` | HecTime | Start time of the record |
| `end_time` | HecTime | End time of the record |
| `interval` | int | Interval in seconds (positive for regular, negative for irregular) |
| `granularity` | int | Time granularity in seconds |
| `tzid` | str | Timezone identifier |
| `nodata` | ndarray of bool | Boolean mask where True = missing value |
| `empty` | bool | True if all values are missing |

---

## Example 2 — Read with a Time Window

Read a subset of a time series by specifying a `(start, end)` window.

```python
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR//"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(
        pathname,
        window=("15JUL2019 2300", "16JUL2019 0100"),
    )

    times = [t.datetime() for t in ts.times]
    values = ts.values.tolist()
    print("Times:", times)
    print("Values:", values)
```

**Window format:**

- A tuple of two date/time strings: `(start_date, end_date)`.
- Accepts any format that `HecTime` can parse (see HecTime Quickstart).
- Common formats: `"15JUL2019 2300"`, `"15Jul2019 23:00"`,
  `"2019-07-15T23:00:00"`.

---

## Example 3 — Read with Trimming

By default, `read_ts()` returns the full date range including leading and
trailing missing values. Use `trim_missing=True` to remove them.

```python
with HecDss.Open(dss_file) as fid:
    # Without trimming — may have UNDEFINED values at edges
    ts_full = fid.read_ts(pathname)
    print("Full count:", ts_full.count)

    # With trimming — missing values at edges removed
    ts_trimmed = fid.read_ts(pathname, trim_missing=True)
    print("Trimmed count:", ts_trimmed.count)
```

`trim_missing` only applies to **regular** time series. It removes leading
and trailing `UNDEFINED` values from the returned array.

---

## Example 4 — Read an Irregular Time Series

Irregular time series have variable timestamps. The E-part of the pathname
uses an `IR-` prefix (e.g., `IR-DAY`, `IR-DECADE`).

```python
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/IRREGULAR/TIMESERIES/PARAM//IR-Decade//"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(pathname)

    print("Type:", ts.dtype)    # "Irregular TimeSeries"

    times = [t.datetime() for t in ts.times]
    values = ts.values.tolist()

    for t, v in zip(times, values):
        print(f"  {t} -> {v}")
```

**Irregular time series window flags:**

When reading with a time window, the `window_flag` parameter controls how
boundary values are handled:

| Flag | Behavior |
|------|----------|
| 0 | Strictly adhere to the time window (default) |
| 1 | Also retrieve one value immediately before the window start |
| 2 | Also retrieve one value immediately after the window end |
| 3 | Retrieve one value before and one value after the window |

```python
with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(
        pathname,
        window=("01JAN2019 0000", "01JAN2020 0000"),
        window_flag=1,  # include one value before start
    )
```

---

## Example 5 — Write a Regular Time Series

Build a `TimeSeriesContainer`, populate it, and write to DSS.

```python
from pydsstools.core import TimeSeriesContainer, UNDEFINED
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/EXAMPLE/"

with HecDss.Open(dss_file) as fid:
    count = 4
    interval = 1  # positive = regular time series

    tsc = TimeSeriesContainer(pathname, count, interval)
    tsc.start_time = "01JAN2025 23:00"
    tsc.data_units = "cfs"
    tsc.data_type = "INST"
    tsc.tzid = "UTC"
    tsc.values = [10, 20, UNDEFINED, 40]  # UNDEFINED marks missing data

    fid.put_ts(tsc)
```

**TimeSeriesContainer construction:**

```python
tsc = TimeSeriesContainer(pathname, count, interval)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `pathname` | str | DSS pathname with valid E-part interval |
| `count` | int | Number of values |
| `interval` | int | Positive for regular, negative for irregular |

**Required properties for regular time series:**

| Property | Type | Description |
|----------|------|-------------|
| `start_time` | str or HecTime | Starting date/time |
| `values` | list, ndarray, or array | Time series values |
| `data_units` | str | Units (e.g., `"cfs"`, `"ft"`) |
| `data_type` | str | Type (e.g., `"INST"`, `"PER-AVER"`, `"PER-CUM"`) |

**Optional properties:**

| Property | Type | Description |
|----------|------|-------------|
| `tzid` | str | Timezone identifier (e.g., `"UTC"`) |

---

## Example 6 — Write a Regular Time Series (Keyword Arguments)

Instead of creating a `TimeSeriesContainer`, you can pass keyword arguments
directly to `put_ts()` with a pathname.

```python
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/KWARGS/"

with HecDss.Open(dss_file) as fid:
    fid.put_ts(
        pathname,
        values=[10, 20, 30, 40, 50],
        start_time="01JAN2025 15:00",
        data_units="ft",
        data_type="INST",
        tzid="UTC",
    )
```

When `put_ts()` receives a pathname string instead of a `TimeSeriesContainer`,
it automatically:

1. Determines the interval from the E-part of the pathname.
2. Creates a `TimeSeriesContainer` internally from the keyword arguments.
3. Writes the data to the DSS file.

---

## Example 7 — Write an Irregular Time Series

Irregular time series require explicit timestamps for each value.

```python
from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/A/B/C//IR-DAY/EXAMPLE/"

with HecDss.Open(dss_file) as fid:
    times = [
        "02JUL2010 1200",
        "05JAN2012 0000",
        "15MAR2014 0200",
        "25FEB2018 0500",
        "19DEC2024 1200",
    ]
    values = [1, 20, 30, 40, 50]

    fid.put_ts(
        pathname,
        values=values,
        times=times,
        julian_base="01JAN2000",
        data_units="ft",
        data_type="INST",
        tzid="UTC",
    )
```

**Key differences for irregular time series:**

| Regular | Irregular |
|---------|-----------|
| E-part: `1HOUR`, `1DAY`, etc. | E-part: `IR-DAY`, `IR-DECADE`, etc. |
| Needs `start_time` | Needs `times` list |
| `interval` > 0 | `interval` < 0 |
| No `julian_base` | Optional `julian_base` |

---

## Example 8 — Write Irregular Time Series with TimeSeriesContainer

For more control, build the `TimeSeriesContainer` explicitly.

```python
from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/IRREGULAR/TIMESERIES/PARAM//IR-DECADE/EXAMPLE/"

with HecDss.Open(dss_file) as fid:
    times = ["01JAN2019 02:01", "01JAN5000 01:02"]
    values = [2019, 5000]

    tsc = TimeSeriesContainer(pathname, len(values), -1)
    tsc.times = times           # list of date strings
    tsc.values = values
    tsc.data_units = "ft"
    tsc.data_type = "INST"
    tsc.tzid = "UTC"

    fid.put_ts(tsc)
```

**TimeSeriesContainer `times` setter accepts:**

| Input Type | Description |
|------------|-------------|
| list of str | Date/time strings (parsed via HecTime) |
| list of HecTime | HecTime objects |
| list of datetime | Python datetime objects |
| ndarray of int | Raw integer time values |

Times must be in ascending order. A `ValueError` is raised if they are not.

---

## Example 9 — Round-Trip: Read, Modify, Write Back

Read an existing record, modify it, and write it back.

```python
from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname_in  = "/REGULAR/TIMESERIES/FLOW//1HOUR//"
pathname_out = "/REGULAR/TIMESERIES/FLOW//1HOUR/MODIFIED/"

with HecDss.Open(dss_file) as fid:
    # Read
    ts = fid.read_ts(pathname_in, window=("15JUL2019 2300", "16JUL2019 0100"))

    # Modify — scale all values by 1.5
    values = ts.values * 1.5

    # Write back under a new F-part
    count = ts.count
    tsc = TimeSeriesContainer(pathname_out, count, ts.interval)
    tsc.start_time = ts.start_time
    tsc.values = values
    tsc.data_units = ts.data_units
    tsc.data_type = ts.data_type
    fid.put_ts(tsc)
```

---

## Example 10 — Configure DSS Logging

Control the verbosity of HEC-DSS library messages.

```python
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import dss_logging

# Set logging level: "None", "General", "Diagnostic"
dss_logging.config(level="General")

dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"

with Open(dss_file) as fid:
    ts = fid.read_ts(pathname)
```

**Available logging levels:**

| Level | Description |
|-------|-------------|
| `"None"` | Suppress all DSS messages |
| `"General"` | Standard operational messages |
| `"Diagnostic"` | Verbose debugging output |

---

## Example 11 — Check for Missing Data

Use the `nodata` mask and `UNDEFINED` sentinel to handle missing values.

```python
import numpy as np
from pydsstools.core import UNDEFINED
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR//"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(pathname)

    # Boolean mask: True where value is missing
    mask = ts.nodata
    print("Missing values:", mask.sum())

    # Check if entire record is empty
    print("All missing:", ts.empty)

    # Replace missing with NaN for analysis
    values = ts.values.astype(float)
    values[mask] = np.nan
```

---

## Granularity and Overflow

The internal DSS time representation stores timestamps as integer counts of
time units since December 31, 1899 (julian day 0). The **granularity**
setting controls the unit size:

| Granularity | Unit | Max Date Range |
|-------------|------|----------------|
| 60 (default) | Minutes | ~4,000 years |
| 1 | Seconds | ~68 years |

**Second granularity (1) can overflow** for dates far from the julian base.
When writing irregular time series spanning large date ranges with second
precision, consider:

1. Using minute granularity (60) when seconds are not needed.
2. Setting a `julian_base` close to your data range.
3. Writing one value at a time with `prevent_overflow=True`.

---

## DSS Pathname Structure for Time Series

```
/A-Part/B-Part/C-Part/D-Part/E-Part/F-Part/
```

| Part | Typical Use | Example |
|------|-------------|---------|
| A | Collection or project | `REGULAR`, `IRREGULAR` |
| B | Location | `TIMESERIES`, `GAUGE-01` |
| C | Parameter | `FLOW`, `PRECIP`, `STAGE` |
| D | Date block start | `01JUL2019` (can be empty) |
| E | Interval | `1HOUR`, `15MIN`, `1DAY`, `IR-DAY`, `IR-DECADE` |
| F | Version or variant | `OBS`, `MODIFIED`, `EXAMPLE` |

**Common E-part interval specifications:**

| Regular | Irregular |
|---------|-----------|
| `1MIN` | `IR-DAY` |
| `15MIN` | `IR-MONTH` |
| `1HOUR` | `IR-YEAR` |
| `1DAY` | `IR-DECADE` |
| `1MON` | `IR-CENTURY` |
| `1YEAR` | |

When the D-part is empty, `read_ts()` retrieves all available data. When
it contains a date, only that block is read unless a `window` is specified.

---

## API Summary

### Reading

| Method | Returns | Description |
|--------|---------|-------------|
| `fid.read_ts(pathname)` | `TimeSeriesStruct` | Read full time series. |
| `fid.read_ts(pathname, window=(...))` | `TimeSeriesStruct` | Read a time window. |
| `fid.read_ts(pathname, trim_missing=True)` | `TimeSeriesStruct` | Read with edge trimming (regular only). |
| `fid.read_ts(pathname, window_flag=N)` | `TimeSeriesStruct` | Read with boundary control (irregular only). |
| `fid.read_ts(pathname, reg=True)` | `TimeSeriesStruct` | Force read as regular time series. |
| `fid.read_ts(pathname, ireg=True)` | `TimeSeriesStruct` | Force read as irregular time series. |

### Writing

| Method | Description |
|--------|-------------|
| `fid.put_ts(tsc)` | Write a `TimeSeriesContainer` object. |
| `fid.put_ts(pathname, values=..., start_time=...)` | Write regular time series from keyword arguments. |
| `fid.put_ts(pathname, values=..., times=...)` | Write irregular time series from keyword arguments. |

### TimeSeriesContainer Construction

```python
from pydsstools.core import TimeSeriesContainer

# Regular time series
tsc = TimeSeriesContainer(pathname, count, interval)
tsc.start_time = "01JAN2025 1500"        # starting date/time
tsc.values = [10, 20, 30]                # list, ndarray, or array
tsc.data_units = "cfs"                   # value units
tsc.data_type = "INST"                   # INST, PER-AVER, PER-CUM
tsc.tzid = "UTC"                         # timezone (optional)

# Irregular time series
tsc = TimeSeriesContainer(pathname, count, -1)
tsc.times = ["01JAN2019 0200", ...]      # one timestamp per value
tsc.values = [100, 200, ...]             # same length as times
tsc.data_units = "ft"
tsc.data_type = "INST"
tsc.julian_base = "01JAN2000"            # optional reference date
```

**Accepted input types for `values`:** list, tuple, `numpy.ndarray`, or
`array.array`. Internally converted to float32.

**Accepted input types for `times` (irregular only):** list of strings, list
of HecTime, list of datetime, `numpy.ndarray` of int, or `array.array` of int.
