About pydsstools
===

pydsstools is an experimental Cython based Python library to manipulate [HEC-DSS](http://www.hec.usace.army.mil/software/hec-dssvue/) database file. It supports regular/irregular time-series, paired data series and spatial grid records. Currently, this library works only with  Python 3.7+ 64-bit on Windows machine.

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
tsc.startDateTime=datetime.now().strftime('%d %b %Y %H:00')
tsc.numberValues = 5
tsc.units = "cfs"
tsc.type = "INST"
tsc.interval = 1
tsc.values = [100,UNDEFINED,500,5000,10000]

fid = HecDss.Open(dss_file)
fid.deletePathname(tsc.pathname)
status = fid.put(tsc)
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
endDate = "15JUL2019 21:00:00"

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
    grid_array = dataset.read(masked=True)
    profile = dataset.profile
```
![](images/grid_screenshot.PNG)

### Example 10 
Write Spatial Grid record

Notes:
    type options: PER-AVER, PER-CUM, INST-VAL,INST-CUM, FREQ, INVALID
    flipud: 1 (default) -  flips the numpy array upside down as dss array layout is opposite
            0 - numpy array array is stored as it is 
```
import numpy as np
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_in = "/GRID/RECORD/DATA/01jan2001:1200/01jan2001:1300/Ex9/"
pathname_out = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10/"

with Open(dss_file) as fid:
    # get shape and profile from example grid dss record
    dataset_in = fid.read_grid(pathname_in)
    profile_in = dataset_in.profile
    grid_in = dataset_in.read()

    # create random array, update profile and save as grid record
    profile_out = profile_in.copy()
    profile_out.update(type="PER-AVER",nodata=0,transform=dataset_in.transform) # required parameters
    profile_out.update(crs="UNDEFINED",units="ft",tzid="",tzoffset=0,datasource='') # optional parameters
    grid_out = np.random.rand(*grid_in.shape)*100
    fid.put_grid(pathname_out,grid_out,profile_out,flipud=1)
```
![](images/grid_save1.png)
![](images/grid_save2.png)

### Example 11 
Read pathname catalog
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_pattern ="/PAIRED/*/*/*/*/*/"

with Open(dss_file) as fid:
    path_list = fid.getPathnameList(pathname_pattern,sort=1)
    print('list = %r' % path_list)
```

### Example 12 
Copy dss record
```
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_in ="/PAIRED/DATA/FREQ-FLOW///Ex5/"
pathname_out ="/PAIRED/DATA/FREQ-FLOW///Ex12/"

with Open(dss_file) as fid:
    fid.copy(pathname_in,pathname_out)
```

### Example 13 
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
