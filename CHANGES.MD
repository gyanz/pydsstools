pydsstools changelog
================

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
