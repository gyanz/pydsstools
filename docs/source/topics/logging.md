# DSS Logging

This guide covers how to control the verbosity of HEC-DSS C library messages
in **pydsstools** using the `pydsstools.heclib.logging` module.

When pydsstools opens, reads, or writes DSS files the underlying HEC-DSS C
library prints status lines to the console — for example:

```
-----DSS---zopen   Existing file opened, File: mydata.dss
-----DSS---zwrite  Handle 1; Version 7: /Basin/Gauge/Flow/...
```

By default pydsstools keeps this output minimal (open/close events and errors
only). The logging module lets you increase verbosity for debugging or silence
output entirely, using a `get_dss_logger()` factory modelled on Python's own
`logging.getLogger()`.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Level** | How much the C library prints. Ranges from `NONE` (silent) to `INTERNAL_DIAG_2` (full trace). |
| **Method** | The operation category whose level you want to control (e.g. `TS_READ`, `LOCKING`, `OPEN`). |
| **GLOBAL** | Special `Method` that sets the level for all operation categories at once. This is the default when no method is specified. |
| **get_dss_logger()** | Factory function that returns a cached `DssLogger` for a given method — analogous to `logging.getLogger()`. |
| **TERSE** | The pydsstools default level. Limits output to open/close events and errors. The C library's own default is `GENERAL`. |

### Level scale

DSS levels run in the **opposite** direction to Python's `logging` levels:
a higher DSS integer means *more* verbose output (not less).

```
NONE (0) — silent
  │
CRITICAL (1) — errors only
  │
TERSE (2) — open/close events and errors  ← pydsstools default
  │
GENERAL (3) — writes, reads, housekeeping ← C library default
  │
USER_DIAG (4) — input parameters (ASCII output)
  │
INTERNAL_DIAG_1 (5) — internal debug messages
  │
INTERNAL_DIAG_2 (6) — full trace, extremely verbose
```

---

## Example 1 — Increase global verbosity

Raise the level for all operation categories at once using the `GLOBAL`
logger (returned when no argument is passed to `get_dss_logger()`).

```python
from pydsstools.heclib.logging import get_dss_logger, Level

# Show general operational messages (writes, reads, housekeeping)
get_dss_logger().set_level(Level.GENERAL)

# Alternatively, use a string — any case is accepted
get_dss_logger().set_level("general")
```

---

## Example 2 — Reduce verbosity for one noisy group

Leave all other groups unchanged and silence locking messages.

```python
from pydsstools.heclib.logging import get_dss_logger, Level, Method

get_dss_logger(Method.LOCKING).set_level(Level.CRITICAL)

# Equivalent — string name accepted, case-insensitive
get_dss_logger("locking").set_level(Level.CRITICAL)

# Equivalent — integer method ID
get_dss_logger(9).set_level(Level.CRITICAL)
```

---

## Example 3 — Silence all DSS output permanently

```python
from pydsstools.heclib.logging import get_dss_logger, Level

# Using the Level enum
get_dss_logger().set_level(Level.NONE)

# Equivalent string shorthand
get_dss_logger().set_level("none")
```

> **Note:** `Level.NONE` suppresses all output including errors. Use it
> only when you are certain that DSS errors are handled elsewhere.

---

## Example 4 — Silence output for a block only

Use the `suppress()` context manager. The previous level is restored
automatically when the block exits, even if an exception is raised.

```python
from pydsstools.heclib.logging import get_dss_logger
from pydsstools.heclib.dss import HecDss

with HecDss.Open("mydata.dss") as fid:
    # Silence all DSS messages just for this read
    with get_dss_logger().suppress():
        ts = fid.read_ts("/Basin/Gauge/Flow//1HOUR//")
    # Previous level is restored here
```

---

## Example 5 — Temporarily raise verbosity for a block

Use the `at_level()` context manager to enable diagnostic output for a
specific operation, then restore the previous level.

```python
from pydsstools.heclib.logging import get_dss_logger, Level, Method
from pydsstools.heclib.dss import HecDss

with HecDss.Open("mydata.dss") as fid:
    with get_dss_logger(Method.TS_READ).at_level(Level.USER_DIAG):
        ts = fid.read_ts("/Basin/Gauge/Flow//1HOUR//")
    # TS_READ level restored here
```

---

## Example 6 — Use Python logging integers and name strings

`set_level()` accepts Python `logging` module integers and name strings
directly, so existing logging configuration can be forwarded without a
lookup table.

```python
import logging
from pydsstools.heclib.logging import get_dss_logger

get_dss_logger().set_level(logging.WARNING)   # → Level.TERSE
get_dss_logger().set_level(logging.DEBUG)     # → Level.USER_DIAG
get_dss_logger().set_level("warning")         # → Level.TERSE
get_dss_logger("ts_write").set_level("debug") # → Level.USER_DIAG
```

Python logging integers map to DSS levels as follows (the directions are
opposite — a higher Python integer means *less* output):

| Python constant | int | DSS Level |
|-----------------|-----|-----------|
| `logging.CRITICAL` | 50 | `CRITICAL` |
| `logging.ERROR` | 40 | `CRITICAL` |
| `logging.WARNING` | 30 | `TERSE` |
| `logging.INFO` | 20 | `GENERAL` |
| `logging.DEBUG` | 10 | `USER_DIAG` |

> **Note:** `logging.NOTSET` (integer 0) and the string `"notset"` are
> treated as a **no-op** — the call returns without changing the current
> level. This prevents forwarding a Python logger's effective level from
> accidentally silencing DSS output. To silence output, use `Level.NONE`
> or `"none"` explicitly.

---

## Example 7 — Query the current level

The `level` property reads the current level directly from the C library.

```python
from pydsstools.heclib.logging import get_dss_logger, Method

logger = get_dss_logger(Method.TS_READ)
print(logger.level)        # Level.TERSE
print(logger.level.name)   # "TERSE"
print(logger.level.value)  # 2
print(logger)              # DssLogger(TS_READ, level=TERSE)
```

---

## Level reference

| Name | Value | Aliases | Description |
|------|-------|---------|-------------|
| `NONE` | 0 | `NULL` | No messages at all (including errors). Use `"none"` as a string shorthand. |
| `CRITICAL` | 1 | `ERROR` | Error messages only. |
| `TERSE` | 2 | `WARNING` | Open/close events and critical errors. **pydsstools default.** |
| `GENERAL` | 3 | `INFO` | General messages: writes, reads, housekeeping. C library default. |
| `USER_DIAG` | 4 | `DEBUG` | Diagnostic messages including input parameters. ASCII output only. |
| `INTERNAL_DIAG_1` | 5 | — | Internal debug messages (level 1). Not recommended for end-users. |
| `INTERNAL_DIAG_2` | 6 | — | Full internal trace (level 2). Extremely verbose. |

The alias names (`ERROR`, `WARNING`, `INFO`, `DEBUG`) match the Python
`logging` module constants so that both naming conventions work
interchangeably.

---

## Method reference

| Name | ID | Description |
|------|----|-------------|
| `GLOBAL` | 0 | All groups — also sets DSS-6 Fortran layer. Use this for broad level control. |
| `GENERAL` | 1 | General DSS-7 operations. Fans out to all groups but does **not** set the DSS-6 layer. |
| `GET` | 2 | Low-level record-get operations. |
| `PUT` | 3 | Low-level record-put operations. |
| `READ` | 4 | High-level read operations. |
| `WRITE` | 5 | High-level write operations. |
| `PERM` | 6 | Permanent-storage / housekeeping operations. |
| `OPEN` | 7 | File open and close operations. |
| `CHECK` | 8 | Record existence checks. |
| `LOCKING` | 9 | Multi-user file-locking operations. |
| `TS_READ` | 10 | Time-series read operations. |
| `TS_WRITE` | 11 | Time-series write operations. |
| `ALIAS` | 12 | Alias management. |
| `COPY` | 13 | Record copy / duplicate operations. |
| `UTILITY` | 14 | Miscellaneous utility functions. |
| `CATALOG` | 15 | Catalog operations. |
| `FILE_CHECK` | 16 | File-integrity check operations. |
| `JNI` | 17 | Java Native Interface bridge (not used from pure Python). |

### GLOBAL vs GENERAL

Both `Method.GLOBAL` and `Method.GENERAL` fan the level out to all 18 C
library method slots simultaneously. The difference is that `GLOBAL`
additionally writes to the DSS-6 Fortran messaging layer (via `zset6_`),
making it effective for DSS-6 files opened with `zopen6`. `GENERAL` only
covers DSS-7.

**Prefer `GLOBAL`** (the default) when you want a single level for
everything.

---

## Backward compatibility

Earlier pydsstools code used `dss_logging` from `pydsstools.heclib.utils`:

```python
# Old API — still works but raises DeprecationWarning
from pydsstools.heclib.utils import dss_logging
dss_logging.setLevel("General")
dss_logging.config(method=9, level="Critical")
```

These calls delegate to `get_dss_logger()` internally, so state is
consistent regardless of which API is used. Prefer the new API in new code:

```python
# New API
from pydsstools.heclib.logging import get_dss_logger, Level, Method
get_dss_logger().set_level(Level.GENERAL)
get_dss_logger(Method.LOCKING).set_level(Level.CRITICAL)
```
