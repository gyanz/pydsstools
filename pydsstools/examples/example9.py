'''
Read Spatial Grid record
'''
from pydsstools.heclib.dss.HecDss import Open

dss_file = "DailyTemp7.dss"

pathname = "/SHG/MAXTEMP/DAILY/01APR1993:0000/01APR1993:2400/PRISM/"

with Open(dss_file) as fid:
    grid = fid.read_grid(pathname,0)
