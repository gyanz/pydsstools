'''
Write irregular time-series data to example.dss
'''
from datetime import datetime,timedelta
from array import array
from random import randrange
from pydsstools.heclib.utils import HecTime
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer

dss_file = "example.dss"

tsc = TimeSeriesContainer()
tsc.granularity_value = 60 #second i.e. minute granularity
tsc.numberValues = 10
tsc.pathname = "/IRREGULAR/TIMESERIES///IR-CENTURY/WRITE/"
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
