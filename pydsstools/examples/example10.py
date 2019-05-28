'''
Read Spatial Grid record
'''
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core import core_heclib

dss_file = "DailyTemp7.dss"

pathname = "/SHG/MAXTEMP/DAILY/01APR1993:0000/01APR1993:2400/PRISM/"

with Open(dss_file) as fid:
    ver = core_heclib.get_grid_version(fid,pathname)
    print("ver= %s"%ver)
    #grid = fid.read_grid(pathname,0)
