pydsstools changelog
================
3.1.0 (06-06-2026)
-----------------
* Location: `LocationInfo` dataclass and DSS-7/DSS-6 location record read/write via `read_ts`, `put_ts`, `read_pd`, `put_pd`
* Vertical Datum: `VerticalDatumInfo` (VDI) read/write for DSS-7 and DSS-6
* Time series: quality flags and notes read/write (`store_flag`, `value_precision`, `quality_notes` params on `read_ts`/`put_ts`)
* Text and array record read/write API (`read_text`, `put_text`, `read_array`, `put_array`)
* Binary record read/write support
* Logging: `pydsstools.heclib.logging` with Pythonic DSS message-level control; `DIAG1`/`DIAG2` aliases added to `Level`; `pydsstools` set as program name in DSS records
* File utilities: `ren_path()`, `path_exists()`, `copy_from_file()`, `copy_file()`, `copy_file_to()`, `convert_version()`, `check_file()`, `export_file()`, `CopyRecordFlag` enum
* `copy_path`: wildcard batch mode, optional `pathname_out`, transform callable, returns count
* `heclib_version()` to query the HEC-DSS C library version and date
* Renamed camelCase public functions to snake_case; full API exposed via `pydsstools.heclib.utils`
* `DssPathName.__eq__` added; D-part and E-part normalized independently in `normalize_period`
* RasterSpatialGrid: VSI wrapper support for compressed rasters in `from_file`
* Fixed grid D/E-part `date_style` in `put_grid`, `put_grid0`, `path_exists`
* Fixed `isinstance` check and property access in `TimeSeriesContainer.to_struct`
* Fixed DSS-6 regular time-series time assertion: use window read instead of trim_missing
* Fixed missing `Datum`, `GridType`, `DataType`, `CompressionMethod` exports in `core/__init__.py`
* Fixed `__all__` mismatches in `heclib`; added import-star smoke tests
* Added `CODE_OF_CONDUCT.md` and `CONTRIBUTING.md`

3.0.2 (05-08-2026)
-----------------
* RasterSpatialGrid: added from_file classmethod and context manager support
* Fixed float32 precision, overflow, and stats robustness in grid write path
* Added unit_factor to RasterSpatialGrid.reproject; fixed nodata defaults
* Input dss_path validated and normalized before opening file

3.0.1 (05-01-2026)
-----------------
* Fixed start_time setter shadowing datetime type; scoped to regular interval series only

3.0.0 (05-01-2026)
-----------------
* First stable 3.x release
* Dropped Python 3.8 support; added Python 3.13 support
* NumPy 2.0 and Cython 3.0 compatibility (builds against NumPy 1.x for 3.9-3.12, 2.x for 3.13+)
* Linux wheels built on manylinux_2_28 with PROJ system dependencies
* Sphinx/ReadTheDocs documentation
* CI: per-Python pytest matrix across Windows and Linux
* TimeSeriesContainer: `start_time` defaults to `times[0]` when omitted; raises if a regular series has no `start_time`
* HecDss.Open: `deletePathname` now uses `search_path`; `search_path` guards against a None catalog
* DssPathName: `_parts` exposed as readonly; API revisions
* Paired data: 0-based indexing; `put_pd` accepts DataFrame input; single-curve write
* HecTime parsing fixes; irregular time-series ordering check
* Removed `pydsstools.utils.contrail` and `pydsstools.utils.usgs` (revised versions will ship in a separate library)

3.0.0b5 (02-09-2026)
-----------------
* Linux wheels upgraded to manylinux_2_28; added PROJ system dependencies

3.0.0b4 (02-08-2026)
-----------------
* Dropped Python 3.8 support; modernized type hints
* NumPy 2.0 and Cython 3.0 compatibility
* Sphinx documentation and ReadTheDocs configuration
* Paired data: 0-based indexing; put_pd accepts DataFrame; single-curve write
* HecTime parsing fixes; irregular time-series ordering check

3.0.0b3 (10-11-2025)
-----------------
* DSS-6 files now raise an error on Linux and Mac (unsupported)
* Pytest corrections for grid version 0 and DSS filename handling

3.0.0b2 (10-09-2025)
-----------------
* TimeSeriesContainer API overhaul: new positional init args (pathname, count, interval);
  properties renamed (startDateTime→start_time, endDateTime→end_time, units→data_units,
  timezone→tzid); values/times/data_type exposed as settable properties
* Fixed HecTime-to-datetime conversion
* Fixed error when DSS record is not found
* Paired data API revisions and additional pytests

3.0.0b1 (09-22-2025)
-----------------
* HEC-DSS 7-IV-1, released July 30, 2025
* Paired data and Gridded data API changes
* Gridded data write support for verion 0 grid
* Added pytests
* Added github action to build, test and publish wheels

2.4.1 (08-27-2025)
-----------------
* Added timezone info to TimeSeriesContainer

2.4.0 (08-13-2025)
-----------------
* Added function to write spatial grid data to HEC-DSS 6 file
* zlib deflate compression as well as no compression are supported
* PRECIP_2_BYTES compression method has not been implemented yet
* Fixed issue with lower_left_xy_from_transform function
* Updated numpy version dependency in toml file
* Binary wheel available in Pypi for python 3.8 to 3.12
* Compiled using VS Studio 2022 and Intel OneAPI HPC Toolkit 2025.2.0576

2.3.2 (01-13-2024)
-----------------
* bug fix

2.3.1 (09-06-2023)
-----------------
* Removed support for Python 3.6 and 3.7 due to lack of Anaconda support for these versions
* Build and package information provided in pyproject.toml
* Using versioneer to specify git tag as the released package version
* Source distribution and wheels released on PyPI

2.3 (05-23-2023)
-----------------
* HEC-DSS 7-IQ, release March 15, 2023
* HecTime bug fix

-----------------
2.2 (09-12-2021)
-----------------
* HEC-DSS 7-IG, release Nov 18, 2021

2.1 (07-24-2021)
-----------------
* Bug fix regular time-series time value (int32) overflow for large time window
* Started using Intel OneAPI 2021 in Windows

2.0 (04-02-2021)
-----------------
* Bug fix grid extents and transform values
* Added grid resampling method

1.9 (03-21-2021)
-----------------
* Grid geo-spatial methods via raster accessor
* Bug fix with HecTime
* Minor change in put_grid method

1.8 (02-26-2021)
-----------------
* HEC-DSS 7-IE, released Feb 11, 2021, headers and libraries included
* Raster accessor attribute for SpatialGridStruct

1.7 (02-21-2021)
-----------------
* HEC-DSS 7-IC, released Jan 22, 2021, headers and libraries included
* Setup.py revised to build extension from source code
* Wheel for Windows (Python 3.6 to 3.9) and Ubuntu 20.04 (Python 3.8)
 
1.6 (06-27-2020)
-----------------
* Changed Spatial Grid Record read and write methods, nodata is handled internally
* Integrated C++ (C++14) library to read DSS-6 Grid Record
* Dynamically linked MSVCRT in Windows
* Bug fix paired data labels

1.5 (05-17-2020)
-----------------
* fixed spatial grid record range limit table
* added python 3.8 support for Windows 10 and Linux
* removed python 3.6 and 3.7 support for Linux
* Windows compilation information ...
* Python 3.6: MSVC 14.0, WIN SDK 10.0.10586.0, Numpy 1.16.4 ...
* Python 3.7: MSVC 14.16, WIN SDK 10.0.17763.0, Numpy 1.16.3 ...
* Python 3.8: MSVC 14.24, WIN SDK 10.0.19041.0, Numpy 1.18.4
* Ubuntu 20.04 LTS compilation information ...
* Python 3.8: GCC 9.3, Numpy 1.18.4

1.4 (11-16-2019)
-----------------
* bug fix related to HEC-DSS time-series date containing 2400 hours
* change in HEC-DSS messaging/logging/messaging
* change in examples

1.3 (09-05-2019)
-----------------
* Added squeeze_file funtion to remove deleted dss records permanently

1.2 (08-19-2019)
-----------------
* Added function to retrieve all pathnames by record type
* Revised few utility function
* HEC-DSS 7 library dated 12 Aug 2019

1.1 (08-11-2019)
-----------------
* Adding logging/messaging output levels

1.0 (08-07-2019)
-----------------
* Cython source code made public
* Added DssLastError class, which gives detain info about last input/output error
* Debugged HecTime and method to write irregular time-series to prevent overflow of time value 
* Added example 14

0.9 (07-26-2019)
-----------------
* Support for Ubuntu 18.04 LTS, Mint 19
* Compiled with gcc 8.3

0.8 (07-23-2019)
-----------------
* Added support for Python 3.6
* Function for paired data label 
* Documentation update

0.7 (07-16-2019)
-----------------
* Bug fix reading time-series data
* Added nodata property in TimeSeriesStruct class to determine missing values
* Allow reading irregular time-series even when pathname D-Part is empty
* Pythonic API for reading and writing data 
* Allow reading and editing subset of Paired data series
* Masked array option for gridded dss record

0.6 (06-22-2019)
-----------------
* Added function to write HEC-DSS grid record

0.5 (06-19-2019)
-----------------
* HEC-DSS 7 C library dated 13 June 2019
* Function to read HEC-DSS grid record

0.4 (05-28-2019)
-----------------
* Compatible with Python 3.7 64-bit, Windows 10
* Extension module compiled with VS 2017 and Intel Compiler 19 Update 3
* Based on experimental version of HEC-DSS 7 C library dated 19 Apr 2019
* Folder/subpackage structure changed
* Examples added
* Added function to read HEC-DSS grid record (not fully working)
* The previous release, compatible with Python 3.4, is still available in branch 0.3.

0.3 (09-29-2018)
-----------------
* Compatible with Python 3.4
* Fixed issue with reading timeseries data. Changed type of returned data (time and value) from typed memory view to numpy array.
* Added 64-bit python support
* API changed (e.g., previous pydsstools.core_heclib is equivalent to pydsstools.core)
* Examples were edited
