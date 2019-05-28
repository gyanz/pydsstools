'''
Delete dss record
'''
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname ="/PAIRED/DATA/STAGE-FLOW///DELETE/"

with Open(dss_file) as fid:
    fid.deletePathname(pathname)
