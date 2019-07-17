'''
Read irregular time-series data


'''
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname = "/IRREGULAR/TIMESERIES/FLOW//IR-DECADE/Ex3/"

with HecDss.Open(dss_file) as fid:
    ts = fid.read_ts(pathname,regular=False,window_flag=0)
    print(ts.pytimes)
    print(ts.values)
    print(ts.nodata)
    print(ts.empty)
