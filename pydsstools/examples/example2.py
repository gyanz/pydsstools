'''
Read and plot regular time-series
'''
from pydsstools.heclib.dss import HecDss
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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

values[ts.nodata] = -9999

# Export timeseries to csv
with open('example2_csv_export.txt','w') as fid:
    fid.write('Time,Value\n')
    for t,val in zip(times.tolist(),values.tolist()):
        fid.write('%s,%s\n'%(t,val))

# Export timeseries to csv using pandas
df = pd.DataFrame({"Time":times,"Value":values})
df.to_csv('example2_csv_pandas.txt',
           sep = ',', 
           index = False)


 
