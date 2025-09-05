'''
Delete dss record
'''
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname ="/PAIRED/DATA/FREQ-FLOW///Ex12/"

with Open(dss_file) as fid:
    fid.deletePathname(pathname)
