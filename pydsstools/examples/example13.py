'''
Copy dss record
'''
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_in ="/PAIRED/DATA/FREQ-FLOW///Ex5/"
pathname_out ="/PAIRED/DATA/FREQ-FLOW///Ex12/"

with Open(dss_file) as fid:
    fid.copy(pathname_in,pathname_out)

