# HecTime

This guide covers the `HecTime` class in **pydsstools** — the datetime
handling system for HEC-DSS files.

`HecTime` stores time internally as two integers: a **julian day** (days
since December 31, 1899) and **seconds since midnight** (0-86400). It
provides parsing, formatting, arithmetic, and conversion to/from Python
`datetime` objects.

## Prerequisites

```python
pip install pydsstools
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Julian Day** | Days since December 31, 1899. Julian day 0 = Dec 31, 1899. January 1, 1900 = julian day 1. |
| **Granularity** | Time precision in seconds. Values: 1 (second), 60 (minute, default), 3600 (hour), 86400 (day). |
| **midnight_as_2400** | When True, midnight is represented as 24:00 of the previous day instead of 00:00 of the current day. |
| **Timestep Value** | Integer encoding of a datetime: `julian * (86400/granularity) + seconds/granularity`. |
| **UNDEFINED_TIME** | Sentinel value for invalid or undefined times. |
| **split_datetime** | Static method that parses a wide variety of datetime string formats into `(date, time)` components. |

### Internal Representation

```
HecTime("15Jul2019 14:30:00")
  _julian = 43661              (days since 31Dec1899)
  _seconds_since_midnight = 52200  (14*3600 + 30*60)
  _granularity = 60            (minute precision)
```

---

## Example 1 — Create from Strings

`HecTime` accepts a wide variety of date/time string formats.

```python
from pydsstools.core import HecTime

# Grid-style format (single colon between date and time)
ht = HecTime("01JAN2000:1200")
print(ht.date())    # "01Jan2000"
print(ht.time())    # "12:00:00"

# Space-separated with colons in time
ht = HecTime("15Jul2019 23:00")

# Space-separated compact time
ht = HecTime("01JAN2000 1430")

# ISO format
ht = HecTime("2000-01-15T10:30:00")

# Date only (time defaults to 00:00)
ht = HecTime("01JAN2000")
print(ht.time())    # "00:00:00"

# With AM/PM
ht = HecTime("Jan 1, 2000 2:30 PM")
```

**Accepted string formats:**

| Format | Example |
|--------|---------|
| Grid style | `"01JAN2000:1200"`, `"01JAN2000:120000"` |
| Space + colon time | `"01JAN2000 12:00"`, `"01JAN2000 12:00:00"` |
| Space + compact time | `"01JAN2000 1200"` |
| ISO/XML | `"2000-01-01T12:00:00"`, `"2000-01-01 12:00:00"` |
| Natural date | `"January 1, 2000 12:00"`, `"Jan 1, 2000 2:30 PM"` |
| Date only | `"01JAN2000"`, `"January 1, 2000"` |

---

## Example 2 — Create from Other Types

```python
from datetime import datetime
from pydsstools.core import HecTime

# From Python datetime
dt = datetime(2000, 1, 1, 12, 0)
ht = HecTime(dt)
print(ht.text())    # "01Jan2000:12:00:00"

# From another HecTime (clone)
ht2 = HecTime(ht)

# From an integer timestep value
# Requires granularity and julian_base
ht = HecTime(100, granularity=60, julian_base="01JAN2000")

# Undefined time
ht = HecTime(None)
print(ht.is_undefined())    # True
```

---

## Example 3 — Access Date and Time Components

```python
from pydsstools.core import HecTime

ht = HecTime("15Jul2019 14:30:45")

# Individual components
print(ht.year())      # 2019
print(ht.month())     # 7
print(ht.day())       # 15
print(ht.hour())      # 14
print(ht.minute())    # 30
print(ht.second())    # 45

# Internal representation
print(ht.julian())                  # Julian day number
print(ht.seconds_since_midnight())  # 52245 (14*3600 + 30*60 + 45)
print(ht.granularity())             # 60 (default)
```

---

## Example 4 — Format Output

```python
from pydsstools.core import HecTime

ht = HecTime("02Jun1985 08:30:00")

# Default DSS format
print(ht.text())                              # "02Jun1985:08:30:00"

# Custom strftime format
print(ht.text(format="%Y-%m-%d %H:%M"))       # "1985-06-02 08:30"
print(ht.text(format="%B %d, %Y at %I:%M %p"))  # "June 02, 1985 at 08:30 AM"

# Date with style codes
print(ht.date())             # "02Jun1985"  (default style 2 -> "2 June 1985" variant)
print(ht.date(date_style=0)) # "June 2, 1985"
print(ht.date(date_style=4)) # "02Jun1985"
print(ht.date(date_style=-13))  # "1985-06-02"

# Time with style codes
print(ht.time())             # "08:30:00"   (style 2)
print(ht.time(time_style=0)) # "0830"
print(ht.time(time_style=1)) # "08:30"
print(ht.time(time_style=2)) # "08:30:00"

# Convert to Python datetime
dt = ht.datetime()    # datetime.datetime(1985, 6, 2, 8, 30)
```

**Date style codes (common):**

| Code | Example |
|------|---------|
| 0 | `"June 2, 1985"` |
| 1 | `"Jun 2, 1985"` |
| 2 | `"2 June 1985"` |
| 4 | `"02Jun1985"` |
| 7 | `"02 Jun 1985"` |
| 104 | `"02JUN1985"` (uppercase) |
| -13 | `"1985-06-02"` (ISO) |
| -111 | `"06/02/1985"` |

Use `HecTime._date_style_codes()` to see all available codes.

**Time style codes:**

| Code | Example |
|------|---------|
| 0 | `"0830"` |
| 1 | `"08:30"` |
| 2 | `"08:30:00"` |

---

## Example 5 — Time Arithmetic

`HecTime` supports adding and subtracting time intervals. All arithmetic
methods modify the object in place.

```python
from pydsstools.core import HecTime

ht = HecTime("01Jan2000 12:00:00")

# Add time units
ht.add_seconds(90)       # +1min 30sec
print(ht.time())         # "12:01:30"

ht.add_minutes(45)       # +45min
print(ht.time())         # "12:46:30"

ht.add_hours(6)          # +6 hours
print(ht.time())         # "18:46:30"

ht.add_days(10)          # +10 days
print(ht.date())         # "11Jan2000"

# Subtract (use negative values)
ht.add_days(-5)
print(ht.date())         # "06Jan2000"

# General interval: add_time(interval_seconds, periods)
ht.add_time(3600, 3)     # Add 3 hours
ht.add_time(86400, -2)   # Subtract 2 days
```

**Arithmetic methods:**

| Method | Description |
|--------|-------------|
| `add_seconds(n)` | Add `n` seconds (negative to subtract) |
| `add_minutes(n)` | Add `n` minutes |
| `add_hours(n)` | Add `n` hours |
| `add_days(n)` | Add `n` days |
| `add_time(interval, periods)` | Add `periods` intervals of `interval` seconds |
| `add_delta(relativedelta)` | Add a `dateutil.relativedelta` (for months/years) |

---

## Example 6 — Add Months and Years with relativedelta

For calendar-aware arithmetic (adding months or years), use
`dateutil.relativedelta`:

```python
from dateutil.relativedelta import relativedelta
from pydsstools.core import HecTime

ht = HecTime("01Jan2000 12:00:00")

# Add 2 months and 5 days
ht.add_delta(relativedelta(months=2, days=5))
print(ht.date())    # "06Mar2000"

# Add 1 year
ht.add_delta(relativedelta(years=1))
print(ht.date())    # "06Mar2001"
```

`add_delta()` converts to a Python `datetime`, applies the delta, then
converts back to HecTime. This correctly handles month length variations
and leap years.

---

## Example 7 — Clone to Preserve Originals

Since arithmetic methods modify the object in place, use `clone()` to
create a copy before modifying.

```python
from pydsstools.core import HecTime

ht1 = HecTime("01Jan2000 12:00:00")
ht2 = ht1.clone()

ht2.add_hours(6)

print(ht1.time())    # "12:00:00" — original unchanged
print(ht2.time())    # "18:00:00" — clone modified
```

---

## Example 8 — Midnight Representation

DSS uses two conventions for midnight:

- **00:00 of the current day** (`midnight_as_2400=False`, default)
- **24:00 of the previous day** (`midnight_as_2400=True`)

This matters for period-ending timestamps (e.g., a daily total ending at
midnight).

```python
from pydsstools.core import HecTime

# Default: midnight = 00:00 of Jan 1
ht = HecTime("01JAN2000 00:00", midnight_as_2400=False)
print(ht.date(), ht.time())    # "01Jan2000" "00:00:00"

# Alternative: midnight = 24:00 of Dec 31
ht = HecTime("01JAN2000 00:00", midnight_as_2400=True)
print(ht.date(), ht.time())    # "31Dec1999" "24:00:00"

# Toggle representation
ht.set_midnight_as_2400(False)
print(ht.date(), ht.time())    # "01Jan2000" "00:00:00"
```

The internal absolute time is the same in both cases — only the display
changes. When `midnight_as_2400=True`, midnight causes the julian day to
decrease by 1 and seconds to become 86400.

---

## Example 9 — Timestep Values and Granularity

The `value()` method converts a HecTime to a single integer "timestep
value" used internally by the DSS library.

```python
from pydsstools.core import HecTime

ht = HecTime("02JAN2019 00:00", granularity=60)
print("Minute value:", ht.value())     # Large integer (minutes since epoch)

ht = HecTime("02JAN2019 00:00:10", granularity=1)
print("Second value:", ht.value())     # Even larger (seconds since epoch)
# WARNING: second granularity can overflow for dates far from epoch!

# Safe second granularity with julian_base
ht = HecTime("02JAN2019 00:10", granularity=1, julian_base="01JAN2000")
print("Value with base:", ht.value())  # Smaller, safe value
```

**Granularity settings:**

| Value | Unit | Precision | Max Range |
|-------|------|-----------|-----------|
| 86400 | Day | 1 day | Unlimited |
| 3600 | Hour | 1 hour | Unlimited |
| 60 | Minute | 1 minute | ~4,000 years |
| 1 | Second | 1 second | ~68 years from base |

Use minute granularity (60) unless you specifically need sub-minute
precision. When using second granularity, set a `julian_base` close to
your data dates to prevent integer overflow.

---

## Example 10 — Parse Date/Time Strings with split_datetime

The static method `split_datetime()` breaks a datetime string into its
date and time components without creating a full HecTime object.

```python
from pydsstools.core import HecTime

# ISO format
print(HecTime.split_datetime("2000-01-15T10:30:00"))
# ('2000-01-15', '10:30:00')

# Grid style (single colon)
print(HecTime.split_datetime("01JAN2000:1030"))
# ('01JAN2000', '1030')

# Space + colon time
print(HecTime.split_datetime("Jan 1, 2000 10:30 AM"))
# ('Jan 1, 2000', '10:30 AM')

# Date only
print(HecTime.split_datetime("01JAN2000"))
# ('01JAN2000', '')

# Undefined
print(HecTime.split_datetime("undefined"))
# ('', '')
```

The parser tries multiple strategies in order:

1. Check for `None` or `"undefined"`
2. Try `dateutil.parser` for date-only detection
3. Try regex patterns: ISO, Grid, Colon time, Plain time
4. Fall back to `dateutil` for complex formats
5. Raise `ValueError` if all strategies fail

---

## Example 11 — Undefined Times

`HecTime(None)` creates an undefined time. Undefined times are safe to
use — all methods return sentinel values without raising exceptions.

```python
from pydsstools.core import HecTime

ht = HecTime(None)

print(ht.is_undefined())    # True
print(ht.date())             # "UNDEFINED"
print(ht.time())             # "UNDEFINED"
print(ht.text())             # None
print(ht.datetime())         # None
print(ht.year())             # None
print(ht.value())            # UNDEFINED_TIME constant

# Arithmetic on undefined time is a no-op
ht.add_hours(6)
print(ht.is_undefined())    # Still True
```

---

## Example 12 — Using HecTime with Time Series

HecTime is used throughout the time-series API for timestamps and time
windows.

```python
from pydsstools.core import HecTime
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR//"

with HecDss.Open(dss_file) as fid:
    # Window dates are parsed by HecTime internally
    ts = fid.read_ts(pathname, window=("15JUL2019 2300", "16JUL2019 0100"))

    # Start and end times are HecTime objects
    print("Start:", ts.start_time.text())
    print("End:", ts.end_time.text())

    # Iterator yields HecTime objects
    for ht in ts.times:
        print(f"  {ht.date()} {ht.time()} -> {ht.datetime()}")
```

---

## API Summary

### Construction

| Input | Example |
|-------|---------|
| String | `HecTime("01Jan2000:1200")` |
| datetime | `HecTime(datetime(2000, 1, 1, 12))` |
| HecTime (clone) | `HecTime(existing_ht)` |
| Integer timestep | `HecTime(100, granularity=60, julian_base="01Jan2000")` |
| Undefined | `HecTime(None)` |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `granularity` | int | 60 | Time precision in seconds (1, 60, 3600, 86400) |
| `midnight_as_2400` | bool | False | Midnight as 24:00 of previous day |
| `date_style` | int | 2 | Date formatting style code |
| `time_style` | int | 2 | Time formatting style code |
| `julian_base` | int or str | 0 | Base julian day (only for int input) |

### Properties and Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `julian()` | int | Julian day (days since Dec 31, 1899) |
| `seconds_since_midnight()` | int | Seconds since midnight (0-86400) |
| `granularity()` | int | Time precision in seconds |
| `value()` | int | Encoded timestep value |
| `date(style)` | str | Formatted date string |
| `time(style)` | str | Formatted time string |
| `text(format)` | str | Combined datetime string |
| `datetime()` | datetime | Python datetime object |
| `year()` | int | Year component |
| `month()` | int | Month component (1-12) |
| `day()` | int | Day component (1-31) |
| `hour()` | int | Hour component (0-24) |
| `minute()` | int | Minute component (0-59) |
| `second()` | int | Second component (0-59) |
| `is_undefined()` | bool | True if time is undefined |
| `midnight_as_2400()` | bool | Current midnight mode |
| `clone()` | HecTime | Create a copy |

### Arithmetic Methods

| Method | Description |
|--------|-------------|
| `add_seconds(n)` | Add `n` seconds |
| `add_minutes(n)` | Add `n` minutes |
| `add_hours(n)` | Add `n` hours |
| `add_days(n)` | Add `n` days |
| `add_time(interval, periods)` | Add `periods` of `interval` seconds |
| `add_delta(relativedelta)` | Add months/years via `dateutil.relativedelta` |
| `set_midnight_as_2400(flag)` | Toggle midnight representation |
| `normalize_time()` | Fix overflow/underflow in seconds |

### Static Methods

| Method | Description |
|--------|-------------|
| `split_datetime(s)` | Parse string into `(date, time)` tuple |
| `_date_style_codes()` | Get all date formatting codes |
| `_time_style_codes()` | Get all time formatting codes |
