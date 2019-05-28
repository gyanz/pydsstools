'''
Read and plot regular time-series data from example.dss
'''
from datetime import datetime
from pydsstools.heclib.dss import HecDss
import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np

dss_file = "example.dss"

pathname = "/REGULAR/TIMESERIES/FLOW//1DAY/READ/"
startDay = "10MAR2006"
startTime ="24:00"
endDay = "09APR2006"
endTime = "24:00"

with HecDss.Open(dss_file) as fid:
    tsc = fid.read_window(pathname,startDay,startTime,endDay,endTime)
    #tsc = fid.read_path(pathname)
    times = tsc.pytimes
    values = tsc.values
    print("times = {}".format(times))
    print("values = {}".format(values))

    plt.plot(times,values,"o")
    plt.ylabel(tsc.units)
    plt.gca().xaxis.set_major_locator(dates.DayLocator())
    plt.gca().xaxis.set_major_formatter(dates.DateFormatter("%d%b%Y"))
    plt.show()
