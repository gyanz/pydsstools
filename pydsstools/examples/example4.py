'''
Read paired data-series
'''
from datetime import datetime
from pydsstools.heclib.dss import HecDss
from pydsstools.heclib.util import getDateTimeValues

dss_file = "example.dss"
pathname ="/PAIRED/DATA/STAGE-FLOW///READ/"

fid = HecDss.Open(dss_file)
# read paired data as pandas dataframe
df = fid.read_pd(pathname)
print(df)
fid.close()
