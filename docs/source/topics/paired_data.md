# Paired Data

This guide covers reading, writing, and managing paired data records in
HEC-DSS files using **pydsstools**.

Paired data records store tabular relationships between an independent variable
(x-axis) and one or more dependent variables (y-axis curves). Common uses
include stage-discharge rating curves, frequency-flow relationships,
elevation-area-volume tables, and damage-stage functions.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Paired Data** | A table of x-values mapped to one or more y-value curves. DSS record type 200 (float) or 205 (double). |
| **PairedDataContainer** | Write-side container. Holds pathname, shape, x/y data, units, types, and labels before writing to DSS. |
| **PairedDataStruct** | Read-side structure returned by the Cython layer. Wraps the C `zStructPairedData` and exposes x/y arrays. |
| **Curve** | A single column of y-values sharing the same x-ordinates. A paired data record can hold many curves. |
| **Label** | An optional name for each curve (e.g., "1999", "Stage", "Flow"). |
| **Shape** | `(rows, cols)` — rows is the number of data points per curve, cols is the number of curves. |
| **Window** | An index tuple for reading or writing a sub-region of the table. |
| **Preallocated Record** | A paired data record with space reserved for curves to be filled in later, one at a time. |

### Data Layout

```
              Curve 0    Curve 1    Curve 2
x[0]          y[0,0]     y[0,1]     y[0,2]
x[1]          y[1,0]     y[1,1]     y[1,2]
x[2]          y[2,0]     y[2,1]     y[2,2]
 ...           ...        ...        ...
x[rows-1]    y[r-1,0]   y[r-1,1]   y[r-1,2]
```

- All curves share the same x-ordinates.
- Internally, curves are stored as rows in the C array (each row = one curve).
  The Python API transposes this so that each curve becomes a column in a
  DataFrame.

---

## Example 1 — Read Paired Data as DataFrame

The most common use case. `read_pd()` returns a `pandas.DataFrame` with
x-values as the index, curves as columns, and a two-level column index
(primary name and label).

```python
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname = "/PAIREDDATA/COWLITZ/FREQ-FLOW////"

with HecDss.Open(dss_file) as fid:
    df = fid.read_pd(pathname)
    print(df)
    print("Index (x-values):", df.index.tolist())
    print("Column labels:", df.columns.get_level_values("labels").tolist())
```

**What the DataFrame looks like:**

```
                 y0
labels         1999
x_data
0.950000       30.0
0.800000       40.0
0.600000       54.0
0.500000       60.0
...
```

**Column index structure:**

The DataFrame has a `MultiIndex` on columns with two levels:

- `primary` — sequential identifier (`y0`, `y1`, `y2`, ...)
- `labels` — the curve label string from the DSS record

This design ensures columns always have a unique programmatic name (`y0`, `y1`)
even when labels are missing or duplicated.

---

## Example 2 — Read Paired Data with a Window

Read a subset of rows and curves using the `window` parameter. The window
is a 4-tuple of 0-based, inclusive indices:
`(row_start, row_end, col_start, col_end)`.

```python
with HecDss.Open(dss_file) as fid:
    # Read rows 2-5 (inclusive), all curves
    df = fid.read_pd(pathname, window=(2, 5, 0, None))
    print(df)

    # Read all rows, first curve only
    df = fid.read_pd(pathname, window=(0, None, 0, 0))
    print(df)

    # Read last 3 rows, last 2 curves (negative indices supported)
    df = fid.read_pd(pathname, window=(-3, None, -2, None))
    print(df)
```

**Window indexing rules:**

| Feature | Behavior |
|---------|----------|
| Base | 0-based |
| Bounds | Inclusive at both ends |
| `None` for start | Defaults to first index (0) |
| `None` for end | Defaults to last index |
| Negative indices | Wrapped Python-style (`-1` = last) |
| Overflow end | Clipped to last valid index |
| Invalid range | Raises `IndexError` |

---

## Example 3 — Read as PairedDataStruct (Low-Level)

For lower-level access without the pandas dependency, pass `dataframe=False`
to get the raw `PairedDataStruct`.

```python
with HecDss.Open(dss_file) as fid:
    pds = fid.read_pd(pathname, dataframe=False)

    print("Shape:", pds.shape)          # (rows, cols)
    print("X units:", pds.x_units)      # e.g., "ft"
    print("Y units:", pds.y_units)      # e.g., "cfs"
    print("X type:", pds.x_type)        # e.g., "linear"
    print("Y type:", pds.y_type)        # e.g., "linear"
    print("Labels:", pds.y_labels)      # e.g., ["1999"]

    x, y, labels = pds.get_data()
    # x: shape (1, rows) — single row of x-ordinates
    # y: shape (cols, rows) — each row is one curve
```

**PairedDataStruct properties:**

| Property | Type | Description |
|----------|------|-------------|
| `x_data` | array (1, rows) | X-ordinate values (shared by all curves) |
| `y_data` | array (cols, rows) | Y-values; each row is one curve |
| `shape` | tuple | (rows, cols) |
| `rows` | int | Number of data points per curve |
| `cols` | int | Number of curves |
| `x_units` | str | Units of the independent axis |
| `y_units` | str | Units of the dependent axis |
| `x_type` | str | Type of x-axis (e.g., "linear") |
| `y_type` | str | Type of y-axis (e.g., "linear") |
| `y_labels` | list[str] | Label for each curve |

---

## Example 4 — Query Record Info and Labels

Get metadata about a paired data record without reading the full dataset.

```python
with HecDss.Open(dss_file) as fid:
    # Record dimensions and metadata
    info = fid.pd_info(pathname)
    print(f"Curves: {info['curve_no']}")
    print(f"Points per curve: {info['data_no']}")
    print(f"Label size: {info['label_size']}")

    # Label mapping (primary name -> label string)
    labels = fid.read_pd_labels(pathname)
    print(labels)  # e.g., {'y0': '1999'}
```

`pd_info()` returns:

| Key | Type | Description |
|-----|------|-------------|
| `curve_no` | int | Number of curves (columns) |
| `data_no` | int | Number of data points (rows) |
| `dtype` | int | DSS data type code (200 = float, 205 = double) |
| `label_size` | int | Average label size in characters |

---

## Example 5 — Write Paired Data with PairedDataContainer

Build a `PairedDataContainer`, populate it with data, and write to DSS.

```python
from pydsstools.core import PairedDataContainer
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/BASIN/LOCATION/STAGE-FLOW///EXAMPLE/"
rows = 5
curves = 2

with HecDss.Open(dss_file) as fid:
    pdc = PairedDataContainer(pathname, (rows, curves))
    pdc.x_data = [100, 200, 300, 400, 500]
    pdc.y_data = [
        [10, 20, 30, 40, 50],       # Curve 0
        [15, 25, 35, 45, 55],       # Curve 1
    ]
    pdc.x_units = "ft"
    pdc.x_type = "linear"
    pdc.y_units = "cfs"
    pdc.y_type = "linear"
    pdc.y_labels = ["Rating 2020", "Rating 2021"]
    fid.put_pd(pdc)
```

**PairedDataContainer shape convention:**

`shape = (rows, cols)` where:

- `rows` = number of data points per curve (length of `x_data`)
- `cols` = number of curves (number of sub-arrays in `y_data`)

`y_data` is set as a list of lists (or 2-D array) where each sub-list is one
curve. Internally this is stored as a `(cols, rows)` C-contiguous float32
array.

---

## Example 6 — Write Paired Data from a DataFrame

Pass a pathname and a DataFrame directly to `put_pd()`. The DataFrame index
becomes x-data, and each column becomes a curve.

```python
import pandas as pd
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/BASIN/LOCATION/STAGE-FLOW///FROM-DF/"

df = pd.DataFrame(
    {
        "Rating 2020": [10, 20, 30, 40, 50],
        "Rating 2021": [15, 25, 35, 45, 55],
    },
    index=[100, 200, 300, 400, 500],
)

with HecDss.Open(dss_file) as fid:
    fid.put_pd(
        pathname,
        y_data=df,
        x_units="ft",
        x_type="linear",
        y_units="cfs",
        y_type="linear",
    )
```

**How the DataFrame is mapped:**

| DataFrame Part | DSS Field |
|----------------|-----------|
| `df.index` | x-ordinates |
| Each column | One curve of y-values |
| Column names | Curve labels |
| `df.values.T` | Internal `(cols, rows)` y-data array |

If the DataFrame has a MultiIndex on columns with a level named `"labels"`,
those labels are used instead of the column names.

---

## Example 7 — Preallocate and Fill Curves Individually

For large datasets or incremental writes, preallocate an empty record and
fill it one curve at a time.

### Step 1 — Preallocate

```python
from pydsstools.heclib.dss import HecDss

dss_file = "output.dss"
pathname = "/PAIRED/RESERVOIR/ELEV-AREA///PREALLOC/"
rows = 100
cols = 5

with HecDss.Open(dss_file) as fid:
    fid.preallocate_pd(
        pathname,
        shape=(rows, cols),
        x_units="ft",
        y_units="acres",
        label_size=31,        # characters reserved per label
    )
```

`label_size` controls how many characters are allocated for each curve label.
This determines the maximum label length; labels longer than this are
truncated. The minimum is 12 characters.

### Step 2 — Write individual curves

```python
with HecDss.Open(dss_file) as fid:
    # Write full curve to column 0
    y_values = [i * 2.0 for i in range(rows)]
    fid.put_pd(pathname, col_index=0, y_data=y_values, y_labels=["Pool Area"])

    # Write full curve to column 1, keeping default label
    y_values = [i * 3.0 for i in range(rows)]
    fid.put_pd(pathname, col_index=1, y_data=y_values)

    # Write partial curve to column 2 (rows 10-19 only)
    partial = [99.0] * 10
    fid.put_pd(pathname, col_index=2, y_data=partial, window=(10, 19))
```

**Key points about preallocated records:**

- `col_index` is 0-based in the Python API (converted to 1-based internally).
- `window` for partial writes is `(row_start, row_end)`, 0-based, inclusive.
- If `y_labels` is omitted or empty, the existing label is preserved.
- If `y_labels` is provided, the label is updated (truncated to `label_size`).
- The number of values in `y_data` must not exceed the available row range.

---

## Example 8 — Round-Trip: Read, Modify, Write Back

Read an existing record, modify it, and write it back under a new pathname.

```python
import numpy as np
from pydsstools.heclib.dss import HecDss

dss_file = "sample.dss"
pathname_in  = "/PAIREDDATA/COWLITZ/FREQ-FLOW////"
pathname_out = "/PAIREDDATA/COWLITZ/FREQ-FLOW///MODIFIED/"

with HecDss.Open(dss_file) as fid:
    # Read
    df = fid.read_pd(pathname_in)

    # Modify — scale all y-values by 1.1
    df.iloc[:, :] = df.values * 1.1

    # Write back under a new F-part
    fid.put_pd(
        pathname_out,
        y_data=df,
        x_units="",
        x_type="linear",
        y_units="cfs",
        y_type="linear",
    )
```

When writing back a DataFrame that was originally read with `read_pd()`, the
MultiIndex column structure (with the `"labels"` level) is automatically
picked up by `put_pd()`, preserving the original curve labels.

---

## DSS Pathname Structure for Paired Data

```
/A-Part/B-Part/C-Part/D-Part/E-Part/F-Part/
```

| Part | Typical Use | Example |
|------|-------------|---------|
| A | Collection or project | `PAIREDDATA`, `BASIN` |
| B | Location | `COWLITZ`, `RESERVOIR` |
| C | Parameter pair | `STAGE-FLOW`, `FREQ-FLOW`, `ELEV-AREA` |
| D | Date (often empty for paired data) | ` ` |
| E | Date (often empty for paired data) | ` ` |
| F | Version or variant | `1999`, `MODIFIED`, `PREALLOC` |

For paired data, D-part and E-part are typically empty since the data
represents a relationship rather than a time series.

---

## API Summary

### Reading

| Method | Returns | Description |
|--------|---------|-------------|
| `fid.read_pd(pathname)` | `DataFrame` | Read all data as pandas DataFrame. |
| `fid.read_pd(pathname, window=(...))` | `DataFrame` | Read a sub-region. |
| `fid.read_pd(pathname, dataframe=False)` | `PairedDataStruct` | Read as low-level structure. |
| `fid.read_pd_labels(pathname)` | `dict` | Get `{primary: label}` mapping. |
| `fid.pd_info(pathname)` | `dict` | Get record dimensions and metadata. |

### Writing

| Method | Description |
|--------|-------------|
| `fid.put_pd(pdc)` | Write a `PairedDataContainer` object. |
| `fid.put_pd(pathname, y_data=df, ...)` | Write from a DataFrame. |
| `fid.put_pd(pathname, col_index=i, y_data=[...])` | Write one curve to a preallocated record. |
| `fid.preallocate_pd(pathname, shape=(...))` | Create an empty record for incremental filling. |

### PairedDataContainer Construction

```python
from pydsstools.core import PairedDataContainer

pdc = PairedDataContainer(pathname, (rows, curves))
pdc.x_data = [...]            # list, tuple, or ndarray of length rows
pdc.y_data = [[...], [...]]   # list of curves, each of length rows
pdc.x_units = "ft"            # independent axis units
pdc.x_type = "linear"         # independent axis type
pdc.y_units = "cfs"           # dependent axis units
pdc.y_type = "linear"         # dependent axis type
pdc.y_labels = ["A", "B"]     # one label per curve (optional)
```

**Accepted input types for `x_data`:** list, tuple, `numpy.ndarray`, or
`array.array`. Internally converted to float32.

**Accepted input types for `y_data`:** list of lists, 2-D `numpy.ndarray`, or
tuple of lists. A 1-D input is reshaped to a single curve. Internally
converted to a `(cols, rows)` float32 array.
