# Installation

## From PyPI

Install the latest stable release:

```bash
pip install pydsstools
```

Install a pre-release version (if available):

```bash
pip install --pre pydsstools
```

## Optional Dependencies

For geospatial features (rasterio, geopandas, etc.):

```bash
pip install pydsstools[geo]
```

## Build from Source

1. Clone the repository:

   ```bash
   git clone https://github.com/gyanz/pydsstools.git
   cd pydsstools
   ```

2. *(Optional)* Initialise the HEC-DSS C library submodule:

   Pre-built static libraries (`heclib.lib`, `heclib.a`) are already included in
   the repository, so this step is **only needed if you want to rebuild them from
   source** (e.g. after updating to a newer upstream release).

   ```bash
   git submodule update --init
   ```

   This clones the [hec-dss](https://github.com/HydrologicEngineeringCenter/hec-dss)
   source tree into `pydsstools/src/external/hec-dss/`.
   The submodule tracks the **master** branch (DSS-6 and DSS-7 support).

   To update the submodule to the latest upstream commit later:

   ```bash
   git submodule update --remote
   ```

   See `scripts/build_hecdss.py` for the full rebuild workflow.

3. Build the wheel (requires build tools and a C compiler):

   ```bash
   pip install build
   python -m build
   ```

3. Install the built wheel:

   ```bash
   pip install dist/pydsstools-*.whl
   ```

> **Note:** On Windows, you need Visual Studio Build Tools with C++ workload.
> On Linux, you need `gcc`, `gfortran`, and development headers.
