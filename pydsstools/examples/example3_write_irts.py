'''
Write irregular time-series data

Notes:
     The interval must be [any] integer <= 0 for irregular time-series.
     DParts: IR-MONTH, IR-YEAR, IR-DECADE, IR-CENTURY

'''
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
