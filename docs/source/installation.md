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

2. Build the wheel (requires build tools and a C compiler):

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
