'''
Read and plot regular time-series
'''
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
