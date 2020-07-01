About pydsstools
===

pydsstools is an experimental Cython based Python library to manipulate [HEC-DSS](http://www.hec.usace.army.mil/software/hec-dssvue/) database file. It supports regular/irregular time-series, paired data series and spatial grid records. It is compatible with 64-bit Python on Windows 10 and Ubuntu like linux distributions. For the later, zlib, math, quadmath, and gfortran libraries must be installed. [dssvue](https://github.com/gyanz/dssvue) python library provides graphical user interface for HEC-DSS.    

About HEC-DSS <sup>[1]</sup>
===

HEC-DSS is designed to be optimal for storing and retrieving large sets, or series, of data. HEC-DSS is not a relational database, but a database that is designed to retrieve and store large amounts of data quickly that are not necessarily interlinked to other sets of data, like relational databases are. Additionally, HEC-DSS provides a flexible set of utility programs and is easy to add to a user's application program. These are the features that distinguish HEC-DSS from most commercial relational database programs and make it optimal for scientific applications.

HEC-DSS uses a block of sequential data as the basic unit of storage. Each block contains a series of values of a single variable over a time span appropriate for most applications. The basic concept underlying HEC-DSS is the organization of data into records of continuous, applications-related elements as opposed to individually addressable data items. This approach is more efficient for scientific applications than a relational database system because it avoids the processing and storage overhead required to assemble an equivalent record from a relational database.

Data is stored in blocks, or records, within a file and each record is identified by a unique name called a "pathname." Each time data is stored or retrieved from the file, its pathname is used to access its data. Information about the record (e.g., units) is stored in a "header array." This includes the name of the program writing the data, the number of times the data has been written to, and the last written date and time. HEC-DSS documents stored data completely via information contained in the pathname and stored in the header so no additional information is required to identify it. One data set is not directly related to another so there is no need to update other areas of the database when a new data set is stored. The self-documenting nature of the database allows information to be recognized and understood months or years after it was stored.

Because of the self-documenting nature of the pathname and the conventions adopted, there is no need for a data dictionary or data definition file as required with other database systems. In fact, there are no database creation tasks or any database setup. Both HEC-DSS utility programs and applications that use HEC-DSS will generate and configure HEC-DSS database files automatically. There is also no pre-allocation of space; the software automatically expands the file size as needed.

HEC-DSS references data sets, or records, by their pathnames. A pathname may consist of up to 391 characters and is, by convention, separated into six parts, which may be up to 64 characters each. Each part is delimited by a slashe "/", and is labeled "A" through "F", as follows: /A/B/C/D/E/F/.

A list of the pathnames in a DSS file is called a "catalog." In version 6, the catalog was a separate file; in version 7, the catalog is constructed directly from pathnames in the file.

Multi-user access mode is handled automatically by HEC-DSS. The user does not need to do anything to turn it on. Multi-user access allows multiple users, multiple processes, to read and write to the same HEC-DSS file at the same time. This is true for a network drive as well as a local drive. You can have a shared network HEC-DSS file that has several processes reading and writing to it at the same time. The only drawback is that file access may be slower, depending on the operating system.

 1. USACE, Hydrologic Engineering Center (July, 2019). HEC Data Storage System Guide (Draft).

Changes
===

[**changelog**][changelog]

   [changelog]: https://github.com/gyanz/pydsstools/blob/master/CHANGES.MD

Usage
===

Sample dss file available in examples folder.

### Example 1
Write regular time-series data to example.dss

Notes:
     The interval must be [any] integer greater than 0 for regular time-series.
     Actual time-series interval implied from E-Part of pathname
     The values attribute can be list, array or numpy array

```
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer,UNDEFINED

dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"
tsc = TimeSeriesContainer()
tsc.pathname = pathname
tsc.startDateTime = "15JUL2019 19:00:00"
tsc.numberValues = 7
tsc.units = "cfs"
tsc.type = "INST"
tsc.interval = 1
tsc.values = [100,UNDEFINED,500,5000,10000,24.1,25]

fid = HecDss.Open(dss_file)
fid.deletePathname(tsc.pathname)
fid.put_ts(tsc)
ts = fid.read_ts(pathname)
fid.close()
```

### Example 2
Read and plot regular time-series
```
from pydsstools.heclib.dss import HecDss
import matplotlib.pyplot as plt
import numpy as np

dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"
startDate = "15JUL2019 19:00:00"
endDate = "15AUG2019 19:00:00"

fid = HecDss.Open(dss_file)
ts = fid.read_ts(pathname,window=(startDate,endDate),trim_missing=True)

times = np.array(ts.pytimes)
values = ts.values
plt.plot(times[~ts.nodata],values[~ts.nodata],"o")
plt.show()
fid.close()
```

### Example 3
Write irregular time-series data

Notes:
     The interval must be [any] integer <= 0 for irregular time-series.
     DParts: IR-MONTH, IR-YEAR, IR-DECADE, IR-CENTURY
```
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer, UNDEFINED

dss_file = "example.dss"
pathname = "/IRREGULAR/TIMESERIES/FLOW//IR-DECADE/Ex3/"

tsc = TimeSeriesContainer()
tsc.numberValues = 5
tsc.pathname = pathname
tsc.units ="cfs"
tsc.type = "INST"
tsc.interval = -1
tsc.values = [100,UNDEFINED,500,5000,10000]


tsc.times = [datetime(1900,1,12),datetime(1950,6,2,12),
             datetime(1999,12,31,23,0,0),datetime(2009,1,20),
             datetime(2019,7,15,5,0)]

with HecDss.Open(dss_file) as fid:
    status = fid.put_ts(tsc)
```

### Example 4
Read irregular time-series data
```
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname = "/IRREGULAR/TIMESERIES/FLOW//IR-DECADE/Ex3/"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(pathname,regular=False,window_flag=0)
    print(ts.pytimes)
    print(ts.values)
    print(ts.nodata)
    print(ts.empty)
```

### Example 5 
Write paired data series
```
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import PairedDataContainer

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///Ex5/"

pdc = PairedDataContainer()
pdc.pathname = pathname
pdc.curve_no = 2
pdc.independent_axis = list(range(1,10))
pdc.data_no = 9
pdc.curves = np.array([[5,50,500,5000,50000,10,100,1000,10000],
                       [11,11,11,11,11,11,11,11,11]],dtype=np.float32)
pdc.labels_list = ['Column 1','Elevens']
pdc.independent_units = 'Number'
pdc.dependent_units = 'Feet'

fid = HecDss.Open(dss_file)
fid.put_pd(pdc)
fid.close()
``` 

### Example 6 
Read paired data-series

Notes:
    Row and column/curve indices start at 1 (not zero)
```
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///Ex5/"

#labels_list = ['Column 1','Elevens']

with HecDss.Open(dss_file) as fid:
    read_all = fid.read_pd(pathname)

    row1,row2 = (2,4)
    col1,col2 = (1,2)
    read_partial = fid.read_pd(pathname,window=(row1,row2,col1,col2))
```

### Example 7 
Pre-allocate paired data-series
```
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/PREALLOCATED DATA/FREQ-FLOW///Ex7/"

with HecDss.Open(dss_file) as fid:
    rows = 10
    curves = 15
    fid.preallocate_pd((rows,curves),pathname=pathname)
```

### Example 8 
Write individual curve data in pre-allocated paired data-series 
```
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/PREALLOCATED DATA/FREQ-FLOW///Ex7/"

with HecDss.Open(dss_file) as fid:
    curve_index = 5
    curve_label = 'Column 5'
    curve_data = [10,20,30,40,50,60,70,80,90,100]
    fid.put_pd(curve_data,curve_index,pathname=pathname,labels_list=[curve_label])

    curve_index = 2
    curve_label = 'Column 2'
    curve_data = [41,56,60]
    row1,row2 = (5,7)
    fid.put_pd(curve_data,curve_index,window = (row1,row2),
            pathname=pathname,labels_list=[curve_label])
```

### Example 9 
Read Spatial Grid 
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname = "/GRID/RECORD/DATA/01jan2001:1200/01jan2001:1300/Ex9/"

with Open(dss_file) as fid:
    dataset = fid.read_grid(pathname)
    grid_array = dataset.read()
    profile = dataset.profile
```

### Example 10 
Write Spatial Grid record
 
```
import numpy as np
import numpy.ma as ma
from affine import Affine
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import gridInfo

dss_file = "example.dss"

pathname_out1 = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10a/"
pathname_out2 = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10b/"

with Open(dss_file) as fid:
    # Type 1: data is numpy array
    # np.nan is considered as nodata
    data = np.reshape(np.array(range(100),dtype=np.float32),(10,10))
    data[0] = np.nan # assign nodata to first row
    grid_info = gridInfo()
    cellsize = 100 # feet
    xmin,ymax = (1000,5000) # grid top-left corner coordinates
    affine_transform = Affine(cellsize,0,xmin,0,-cellsize,ymax)
    grid_info.update([('grid_type','specified'),
                      ('grid_crs','unknown'),
                      ('grid_transform',affine_transform),
                      ('data_type','per-aver'),
                      ('data_units','mm'),
                      ('opt_time_stamped',False)])
    fid.put_grid(pathname_out1,data,grid_info)
            
    # Type 2: data is numpy masked array, where masked values are considered nodata
    data = np.reshape(np.array(range(100),dtype=np.float32),(10,10))
    data = ma.masked_where((data >= 10) & (data <30),data) # mask second and third rows
    fid.put_grid(pathname_out2,data,grid_info)

```

### Example 11 
Read DSS-6 Spatial Grid record
Copy DSS-6 Grid to DSS-7 file 

```
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import dss_logging
dss_logging.config(level='Diagnostic')

dss6_file = "example_dss6.dss"
dss7_file = "example.dss"

pathname_in = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/PRISM/"
pathname_out = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/Ex11/"

with Open(dss6_file) as fid:
    dataset = fid.read_grid(pathname_in)
    data = dataset.read()
    profile = dataset.profile

with Open(dss6_file) as fidin, Open(dss7_file) as fidout:
    dataset = fidin.read_grid(pathname_in)
    fidout.put_grid(pathname_out,dataset,compute_range = True) # recomputing range limit table

```

### Example 12 
Read pathname catalog
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_pattern ="/PAIRED/*/*/*/*/*/"

with Open(dss_file) as fid:
    path_list = fid.getPathnameList(pathname_pattern,sort=1)
    print('list = %r' % path_list)
```

### Example 13 
Copy dss record
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_in ="/PAIRED/DATA/FREQ-FLOW///Ex5/"
pathname_out ="/PAIRED/DATA/FREQ-FLOW///Ex12/"

with Open(dss_file) as fid:
    fid.copy(pathname_in,pathname_out)
```

### Example 14 
Delete dss record
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname ="/PAIRED/DATA/FREQ-FLOW///Ex12/"

with Open(dss_file) as fid:
    fid.deletePathname(pathname)
```

Dependencies
===

- [NumPy](https://www.numpy.org)
- [pandas](https://pandas.pydata.org/)
- [affine](https://pypi.org/project/affine/)
- [MS Visual C++ Redistributable for VS 2015 - 2019](https://aka.ms/vs/16/release/vc_redist.x64.exe)

Installation
===
```
python setup.py install 

or

pip install https://github.com/gyanz/pydsstools/zipball/master  
```

Contributing
===
All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.
Feel free to ask questions on my [email](mailto:gyanBasyalz@gmail.com).


License
===
This program is a free software: you can modify and/or redistribute it under [MIT](LICENSE) license. 
