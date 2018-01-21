About pydsstools
===

pydsstools is a Cython/Ctypes based Python library to manipulate [HEC-DSS](http://www.hec.usace.army.mil/software/hec-dssvue/) database file. It allows reading and writing of regular/irregular time-series and paired data series. This library works only with 32-bit Python 3.4 on Windows OS.

API
===
* pydsstools.heclib.dss.HecDss
  * Open(**kwargs) Class
    * read_pd_df(pathname,dtype,copy)
    * getPathnameList(pathname,sort)
    * deletePathname(pathname)
    * members inherited from core_heclib.Open class
* pydsstools.core_heclib
  * Time-Series
    * TimeSeriesStruct
      Object returned when time-series data is read
      * numberValues
      * times
      * values
      * type
      * units
      * pathname
      * granularity       
      * startDate
      * endDate
      * dtype
    * TimeSeriesContainer(**kwargs)
      Container used to store time-series data before writing to file
      * pathname
      * interval
      * granularity_value
      * numberValues
      * times
      * startDateTime
      * units
      * type
      * values
      * values (setter)
  * Paired Data Series
    * PairedDataStruct
      Object returned when paired data series is read
      * curve_no()
      * data_no()
      * get_data()
        Returns tuple  consisting of ordinates,curves and labels
        * labels
        * dataType
    * PairedDataContainer
      Container used to store paired data series before writing to file
      * pathname
      * curve_no
      * data_no
      * curve_mv
        Data (2-D numpy array object) with each row representing a curve of length data_no. The total number of rows must be equal to curve_no.
      * independent_units
        feet, ...
      * independent_type
        linear, ...
      * dependent_units
        feet, ...
      * independent_axis
        1-D python or numpy array containing independent axis values whose length must be equal to data_no.
        * dependent_type
        * labels_list
        * curves
  * Open(**kwargs) Class
    * read_path(pathname,retrieveFlag=-1,boolRetrieveDoubles=1)
    * read_window(pathname,startDate,startTime,endDate,endTime)
    * put(TimeSeriesContainer tsc, storageFlag=0)  
    * copyRecordsFrom(Open copyFrom, pathnameFrom, pathnameTo="")
    * copyRecordsTo(Open copyTo, pathnameFrom, pathnameTo="")
    * read_pd(pathname)
    * prealloc_pd(PairedDataContainer pdc, label_size)
    * put_one_pd(PairedDataContainer pdc, curve_no)
    * put_pd(PairedDataContainer pdc)

Usage
===

Dss file for the examples available in examples folder.

### Example 1
Read and plot time-series data from example.dss

```
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.heclib.util import getDateTimeValues
import matplotlib.pyplot as plt
from matplotlib import dates

dss_file = "example.dss"

pathname = "/REGULAR/TIMESERIES/FLOW/01JAN2006/1DAY/READ/"
startDay = "10MAR2006"
startTime ="24:00"
endDay = "12MAR2006"
endTime = "24:00" 

with HecDss.Open(dss_file) as fid:
    tsc = fid.read_window(pathname,startDay,startTime,endDay,endTime) 
    times = tsc.times
    values = tsc.values
    print("times = {}".format(times))
    print("values = {}".format(values))

    pytimes = [datetime(*getDateTimeValues(x,tsc.granularity_value)) for x in times]
    print("times as python datetime = {}".format(pytimes))
    plt.plot(pytimes,values,"o")
    plt.ylabel(tsc.units)
    plt.gca().xaxis.set_major_locator(dates.DayLocator())
    plt.gca().xaxis.set_major_formatter(dates.DateFormatter("%d%b%Y"))
    plt.show()
```

### Example 2
Write regular time-series data to example.dss
```
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core_heclib import TimeSeriesContainer

dss_file = "example.dss"

tsc = TimeSeriesContainer()
tsc.granularity_value = 60 #seconds i.e. minute granularity 
tsc.numberValues = 10 
tsc.startDateTime="01 JAN 2017 01:00"
tsc.pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/WRITE/" 
tsc.units = "cfs" 
tsc.type = "INST" 
tsc.interval = 1 
#must a +ve integer for regular time-series
#actual interval implied from E part of pathname
tsc.values =np.array(range(10),dtype=np.float32) 
#values may be list,array, numpy array

fid = Open(dss_file)
status = fid.put(tsc)
fid.close()
```

### Example 3
Write irregular time-series data to example.dss
```
from datetime import datetime,timedelta
from array import array
from random import randrange
from pydsstools.heclib.dss import HecDss
from pydsstools.core_heclib import TimeSeriesContainer
from pydsstools.heclib.util import HecTime

dss_file = "example.dss"

tsc = TimeSeriesContainer()
tsc.granularity_value = 60 #second i.e. minute granularity 
tsc.numberValues = 10 
tsc.fullName = "/IRREGULAR/TIMESERIES///IR-CENTURY/WRITE/" 
#IR-MONTH, IR-YEAR, IR-DECADE, IR-CENTURY        
tsc.units ="cfs" 
tsc.type = "INST" 
tsc.interval = -1 
#-1 for specifying irregular time-series
tsc.values = array("d",range(10)) 
#values may be list, python array, or numpy array

times = []
begin = datetime(1899,12,31)
end = datetime(2017,4,18)
for x in range(tsc.numberValues):
    diff = end - begin
    diff_seconds = diff.days*24*60*60 +diff.seconds
    _rand= randrange(diff_seconds)
    new_date = begin+timedelta(seconds=_rand)
    hec_datetime = HecTime(new_date.strftime("%d %b %Y %H:%M"))
    #default granularity is minute 
    times.append(hec_datetime.datetimeValue) 

times = sorted(times) 
#time must be in ascending order in irregular tsc

tsc.times = times

with HecDss.Open(dss_file) as fid:
    status = fid.put(tsc)
```

### Example 4
Read paired data from example.dss:
```
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.heclib.util import getDateTimeValues

dss_file = "example.dss"
pathname ="/PAIRED/DATA/STAGE-FLOW///READ/"

fid = HecDss.Open(dss_file)
# read paired data as pandas dataframe
df = fid.read_pd_df(pathname)
fid.close()
```

### Example 5 
Write paired data series
```
from pydsstools.heclib.dss import HecDss
from pydsstools.core_heclib import PairedDataContainer
from array import array
import numpy as np

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///WRITE/"

fid = HecDss.Open(dss_file)
pdc = PairedDataContainer()

pdc.pathname = pathname
pdc.curve_no = 1
pdc.independent_axis = array('f',[i/10.0 for i in range(1,11)])
pdc.data_no = len(pdc.independent_axis)
pdc.curves = np.array([range(1,10)],dtype=np.float32) 
fid.put_pd(pdc)
fid.close()
``` 

### Example 6 
Pre-allocate Paired Data Series table

from pydsstools.heclib.dss import HecDss
from pydsstools.core_heclib import PairedDataContainer
from array import array

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///PREALLOC WRITE/"
max_column_label_len = 5

pdc = PairedDataContainer()
pdc.pathname = pathname
pdc.curve_no = 10
pdc.independent_axis = array('f',[i/10.0 for i in range(1,11)])
pdc.data_no = len(pdc.independent_axis)
pdc.labels_list=[chr(x) for x in range(65,65+10)]]

fid.prealloc_pd(pdc,max_column_label_len)
fid.close()
```

### Example 7 
Read pathname catalog from example.dss
```
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core_heclib import getPathnameCatalog

dss_file = "example.dss"

pathname_pattern ="/PAIRED/*/*/*/*/*/"

with Open(dss_file) as fid:
    path_list = fid.getPathnameList(pathname_pattern,sort=1)
    print('list = %r' % path_list)
```

### Example 8 
Delete pathname from example.dss
```
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core_heclib import getPathnameCatalog

dss_file = "example.dss"

pathname ="/PAIRED/DATA/STAGE-FLOW///DELETE/"

with Open(dss_file) as fid:
    status = fid.deletePathname(pathname)
    print('return status = %d' % status)
```

Installation
===
To install pymake directly from the git repository type:

pip install 


Contribution
===
All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.
Feel free to ask questions on the my email.


License
===
This program is a free software: you can modify and/or redistribute it under MIT license. 
