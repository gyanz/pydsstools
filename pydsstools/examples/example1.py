'''
Write regular time-series data to example.dss

Notes:
     The interval must be [any] integer greater than 0 for regular time-series.
     Actual time-series interval implied from E-Part of pathname
     The values attribute can be list, array or numpy array

'''
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer,UNDEFINED

dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"
tsc = TimeSeriesContainer()
tsc.pathname = pathname
tsc.startDateTime="15JUL2019 19:00:00"
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
