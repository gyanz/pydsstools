# Gridded Data

DSS gridded records store spatially distributed data — precipitation fields,
temperature surfaces, elevation models — on regular grids tied to a map
projection. Each record carries both the cell values (as a 2-D NumPy array) and
a **GridInfo** metadata object that describes the grid dimensions, cell size,
projection, data units, and compression.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Grid Version 100** | Modern DSS-7 native grid format. Recommended for new data. |
| **Grid Version 0** | Legacy format used in DSS-6 files. Can be read and converted. |
| **GridInfo** | Object holding grid metadata (projection, cell size, shape, units, etc.). |
| **GridType** | Enum for projection type: `hrap`, `albers`, `specified`, or `undefined` (with `_time` variants). |
 | **SpatialGridStruct** | Container returned by `read_grid()` — holds the data array, GridInfo, etc. |
| **UNDEFINED** | Sentinel value representing missing data in DSS grid cells. |

## Grid Type Overview

pydsstools supports four grid projection types:

- **HRAP** — Hydrologic Rainfall Analysis Project polar-stereographic grid
  used by NEXRAD/MPE precipitation products. Fixed cell size of 4762.5 m.
- **Albers (SHG)** — Albers Equal-Area Conic projection, the USACE Standard
  Hydrologic Grid. Common cell sizes are 2000 m and 1000 m.
- **Specified** — User-defined CRS via EPSG code, PROJ string, or WKT.
  Maximum flexibility for custom projections.
- **Undefined** — No projection information. Suitable for generic raster data.

## Grid Coordinate Concepts

DSS grids use two important coordinate parameters to position grids within a
projection system: **coords_cell0** and **lower_left_cell**. These work
differently depending on the grid type.

### For Albers/SHG Grids

Albers grids reference a global coordinate system where the projection origin
is typically (0, 0):

| Parameter | Description |
|-----------|-------------|
| **coords_cell0** | Coordinates of the southwest corner of cell (0, 0) in the global grid system. For SHG (EPSG:5070), this is usually `(0.0, 0.0)` — the projection origin (false easting, false northing). |
| **lower_left_cell** | Cell indices `(x_cell, y_cell)` indicating which cell in the global grid corresponds to your grid's lower-left corner. Calculated as `(floor((xmin - x_0) / cellsize), floor((ymin - y_0) / cellsize))`. |
| **min_xy** | The actual geographic coordinates `(xmin, ymin)` of your grid's lower-left corner in projection units (meters for SHG). |

This design allows multiple grids to be spatially referenced within the same
global SHG coordinate system, even if they cover different regions.

**Example:** A grid covering part of the eastern US might have:
- `coords_cell0 = (0.0, 0.0)` — SHG projection origin
- `lower_left_cell = (-750, 250)` — cell indices relative to origin
- `min_xy = (-1500000, 500000)` — actual coordinates in meters (EPSG:5070)

### For Specified Grids

Specified grids follow the HEC-MetVue convention where the grid's own corner
serves as the reference:

| Parameter | Description |
|-----------|-------------|
| **coords_cell0** | Equals `min_xy` — the actual coordinates of the grid's lower-left corner. |
| **lower_left_cell** | Always `(0, 0)` — the grid is self-referencing. |
| **min_xy** | The geographic coordinates `(xmin, ymin)` of the grid's lower-left corner. |

This simpler convention makes specified grids more portable but requires an
explicit CRS definition.

### Summary Table

| Grid Type | coords_cell0 | lower_left_cell |
|-----------|--------------|-----------------|
| **Albers/SHG** | Projection origin, typically `(0, 0)` | Calculated cell indices (can be negative) |
| **Specified** | Same as `min_xy` | Always `(0, 0)` |
| **HRAP** | HRAP origin coordinates | Calculated cell indices |
| **Undefined** | User-defined or `(0, 0)` | User-defined or `(0, 0)` |

> **Note:** When writing grids with `put_grid()`, the `normalize` parameter
> (default `True`) automatically calculates `coords_cell0` and `lower_left_cell`
> from `min_xy` or the input transform based on the grid type.

---

## Example 1 — Read a Version-100 Grid (DSS-7)

Version-100 is the modern grid format native to DSS-7 files. This example reads
three grids — HRAP, Albers, and Specified — from a single DSS-7 file and
prints their metadata.

```python
from pydsstools.heclib.dss.HecDss import Open

dss_file = "sample_dss/grid7.dss"

with Open(dss_file) as fid:
    # --- HRAP grid (NEXRAD precipitation) ---
    pathname = "/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD/"
    ds = fid.read_grid(pathname)
    data = ds.read()               # numpy masked array of cell values
    gridinfo = ds.gridinfo         # GridInfo metadata (HrapInfo)
    print(gridinfo)
    print("Extra fields:", gridinfo.extra_info)

    # --- Albers/SHG grid ---
    pathname = "/SHG/MARFC/PRECIP/23JUL2003:2300/23JUL2003:2400/NEXRAD (2000 M)/"
    ds = fid.read_grid(pathname)
    print(ds.gridinfo)             # AlbersInfo

    # --- Specified grid (UTM Zone 18N) ---
    pathname = "/UTM_18N/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD (1000 M)/"
    ds = fid.read_grid(pathname)
    print(ds.gridinfo)             # SpecifiedInfo
```

**What happens under the hood:**

1. `Open()` opens the DSS file in a context manager, ensuring the file is
   properly closed when the block exits.
2. `read_grid()` reads the grid record and returns a `SpatialGridStruct`.
3. `.read()` returns the cell values as a NumPy masked array, where nodata
   cells are masked.
4. `.gridinfo` builds and returns the appropriate `GridInfo` subclass
   (`HrapInfo`, `AlbersInfo`, or `SpecifiedInfo`) based on the stored
   projection.
5. `.extra_info` exposes any additional metadata fields stored with the record
   that fall outside the standard schema.

---

## Example 2 — Read a Version-0 Grid (DSS-6, high-level API)

Legacy DSS-6 files store grids in the older version-0 format. The `read_grid()`
method automatically detects the version and converts the record to the modern
format, returning the same `SpatialGridStruct` as version-100 grids.

```python
from pydsstools.heclib.dss.HecDss import Open

dss_file = "sample_dss/grid6.dss"

with Open(dss_file) as fid:
    pathname = "/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD/"
    ds = fid.read_grid(pathname)
    data = ds.read()
    gridinfo = ds.gridinfo
    print(gridinfo)
```

The conversion is transparent — code that works with version-100 grids works
identically with version-0 grids.

> **Note:** There are differences in how grid metadata is stored between
> version-0 and version-100 formats:
>
> - **Compression:** Version-0 uses RLE-style compression for precipitation
>   data, which has no direct equivalent in version-100. When read via
>   `read_grid()`, this appears as *undefined compression* in `gridinfo`.
> - **Projection:** Version-0 stores Albers parameters explicitly, while
>   version-100 stores a WKT string in `crs` (or implies SHG when `crs` is empty).
>
> These differences are handled automatically during conversion. If you need
> to preserve the original version-0 format when writing back, use
> `read_grid2()` instead.

---

## Example 3 — Read a Version-0 Grid (DSS-6, low-level API)

For cases where you need the raw NumPy array and a lightweight `GridInfo6`
structure (without the full `SpatialGridStruct` wrapper), use `read_grid2()`.
This returns a tuple of `(ndarray, GridInfo6)`.

```python
from pydsstools.heclib.dss.HecDss import Open

dss_file = "sample_dss/grid6.dss"

with Open(dss_file) as fid:
    # Returns (numpy_array, GridInfo6) instead of SpatialGridStruct
    data, gridinfo = fid.read_grid2(
        "/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD/"
    )
    print(gridinfo)

    data, gridinfo = fid.read_grid2(
        "/SHG/MARFC/PRECIP/23JUL2003:2300/23JUL2003:2400/NEXRAD (2000 M)/"
    )
    print(gridinfo)
```

**When to use `read_grid2()`:**

- You need to read and write back a version-0 grid while preserving its
  original format (including RLE-style compression for precipitation data).
- You only need the raw array and basic metadata.
- You are working with legacy DSS-6 files and want minimal overhead.
- You do not need the rasterio-backed spatial methods (plotting, masking,
  reprojection).

---

## Example 4 — Write a Grid Record

This example creates a synthetic 10x10 Albers grid from a NumPy array and
writes it to both DSS-7 (version-100) and DSS-6 (version-0) files.

```python
import numpy as np
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType
from pydsstools.core import UNDEFINED

dss7_file = "output/out7.dss"
dss6_file = "output/out6.dss"

pathname = "/GRID-VER{}/RECORD/DATA/01jan2019:1200/02jan2019:0000/Ex10a/"

with Open(dss7_file) as fid7, Open(dss6_file, version=6) as fid6:
    shape = (10, 10)
    cell = 2000                     # cell size in metres
    xmin, ymin = (2000, 4000)       # lower-left corner in Albers coords

    # Build a 10x10 ramp with NaN in the first row
    data = np.arange(100, dtype=np.float64).reshape(shape)
    data[0] = np.nan

    # Create grid metadata via the factory function
    ginfo = GridInfoCreate(
        grid_type=GridType.albers_time,
        shape=shape,
        cell_size=cell,
        data_type=DataType.per_aver,
        data_units="mm",
        min_xy=(xmin, ymin),
    )

    # Write as version-100 (modern) and version-0 (legacy) to DSS-7
    fid7.put_grid(data, pathname.format("100"), ginfo)
    fid7.put_grid0(data, pathname.format("0"), ginfo)

    # Write version-0 to DSS-6, using UNDEFINED sentinel for missing cells
    data[5] = UNDEFINED
    fid6.put_grid0(data, pathname.format("0"), ginfo)
```

**Key points:**

- `GridInfoCreate()` is the recommended factory function. It selects the
  correct `GridInfo` subclass (`AlbersInfo` here) based on `grid_type`.
- `put_grid()` writes version-100 grids (DSS-7 only).
- `put_grid0()` writes version-0 grids (works with both DSS-6 and DSS-7).
- Use `np.nan` for missing data in version-100. Use the `UNDEFINED` sentinel
  for version-0 grids.
- The `min_xy` parameter sets the lower-left corner coordinates of the grid
  extent in projection units.

---

## Example 5 — Copy a Grid from DSS-6 to DSS-7

A common migration task is converting legacy DSS-6 grids to the modern DSS-7
format. Read from the source file with `read_grid()`, then write to the
destination with `put_grid()`.

```python
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import dss_logging

dss_logging.config(level="Diagnostic")

dss6_file = "example_dss6.dss"
dss7_file = "example.dss"

pathname_in  = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/PRISM/"
pathname_out = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/Ex11/"

with Open(dss6_file) as fidin, Open(dss7_file) as fidout:
    dataset = fidin.read_grid(pathname_in)
    fidout.put_grid(pathname_out, dataset, compute_range=True)
```

**Key points:**

- `dss_logging.config(level="Diagnostic")` enables verbose HEC-DSS library
  logging, useful for debugging read/write issues.
- `compute_range=True` tells `put_grid()` to recalculate the histogram range
  table (bin edges and counts) from the data. Use this when writing grids
  whose statistics may have changed or are missing.
- The `dataset` returned by `read_grid()` can be passed directly to
  `put_grid()` — no need to manually extract data and metadata.

---

## Example 6 — Spatial Analysis (Mask, Crop, Plot)

When **rasterio** and **GDAL** are installed, `SpatialGridStruct` exposes a
`.raster` accessor that provides geospatial operations: plotting, masking by
bounding box or polygon, cropping, reprojection, and GeoTIFF export.

```python
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import BoundingBox

dss_file = "example.dss"

pathname     = "/SHG/LCOLORADO/PRECIP/02JAN2020:1500/02JAN2020:1600/Ex15/"
pathname_out = "/SHG/LCOLORADO/PRECIP/02JAN2020:1500/02JAN2020:1600/Ex15 OUT/"

fid = Open(dss_file)
ds = fid.read_grid(pathname)

if ds.raster is not None:
    # Wrap in a RasterSpatialGrid for spatial operations
    grid = ds.raster.inst()
    grid.plot(mask_zeros=True, title="Original Spatial Grid")

    # Mask without cropping — values outside bbox become nodata
    bbox = BoundingBox(-50000, 600000, 50000, 700000)
    clipped = grid.mask(bbox, crop=False)
    clipped.plot(mask_zeros=True, title="Clipped Spatial Grid")

    # Crop to bbox extent — grid dimensions shrink to fit
    cropped = grid.mask(bbox, crop=True)
    cropped.plot(mask_zeros=True, title="Cropped Spatial Grid")

    # Write cropped grid back to DSS
    fid.put_grid(cropped.read(), pathname_out, cropped.gridinfo)
```

**Available spatial operations:**

| Method | Description |
|--------|-------------|
| `grid.plot()` | Render with matplotlib. Supports `mask_zeros`, `cmap`, `colorbar`, `title`. |
| `grid.mask(geom)` | Mask by bounding box, shapefile, or any `__geo_interface__` geometry. |
| `grid.resample(scale)` | Resample by a scale factor within the same CRS. |
| `grid.reproject(dst_crs)` | Reproject to a new CRS (EPSG, PROJ, or WKT). |
| `grid.save_tiff(path)` | Export to GeoTIFF preserving CRS and transform. |
| `grid.generate_contours(path)` | Create contour-line shapefile via GDAL. |
| `grid.gridinfo` | Build GridInfo from the raster profile (useful before `put_grid()`). |

**Requirements:** `rasterio`, `matplotlib`, and optionally `gdal` (for
contours). If `rasterio` is not installed, `.raster` returns `None` and
spatial operations are unavailable.

> **Note:** Geospatial operations on HRAP and Albers grids involve
> internal coordinate conventions that may produce unexpected results
> in edge cases. Feedback on cropped/masked grid metadata accuracy is
> welcome.

---

## DSS Pathname Structure for Grids

Grid pathnames follow the standard DSS 6-part convention:

```
/A-Part/B-Part/C-Part/D-Part/E-Part/F-Part/
```

| Part | Typical Use | Example |
|------|-------------|---------|
| A | Grid collection or projection identifier | `SHG`, `HRAP`, `UTM_18N` |
| B | Location or basin name | `MARFC`, `LCOLORADO` |
| C | Parameter | `PRECIP`, `MAXTEMP` |
| D | Start date/time | `23JUL2003:0000` |
| E | End date/time | `23JUL2003:0100` |
| F | Source or variant label | `NEXRAD`, `PRISM`, `Ex15` |

---

## API Summary

### Reading

| Method | Returns | Use Case |
|--------|---------|----------|
| `fid.read_grid(pathname)` | `SpatialGridStruct` | Standard read; works with both DSS-6 and DSS-7, any grid version. |
| `fid.read_grid(pathname, metadata_only=True)` | `SpatialGridStruct` | Read only metadata (no cell data). |
| `fid.read_grid2(pathname)` | `(ndarray, GridInfo6)` | Low-level read for DSS-6 version-0 grids. |

### Writing

| Method | Description |
|--------|-------------|
| `fid.put_grid(data, pathname, gridinfo)` | Write version-100 grid to DSS-7. |
| `fid.put_grid(pathname, dataset)` | Write a `SpatialGridStruct` directly. |
| `fid.put_grid0(data, pathname, gridinfo)` | Write version-0 grid (DSS-6 or DSS-7). |

### GridInfo Creation

```python
from pydsstools.core.gridinfo import GridInfoCreate, GridType, DataType

ginfo = GridInfoCreate(
    grid_type=GridType.albers_time,
    shape=(100, 150),
    cell_size=2000.0,
    data_type=DataType.per_aver,
    data_units="MM",
    min_xy=(-500000, 200000),
)
```

The factory function accepts any grid type and returns the correct subclass
(`GridInfo`, `HrapInfo`, `AlbersInfo`, or `SpecifiedInfo`).
