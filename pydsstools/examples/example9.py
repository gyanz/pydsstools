'''
Read Spatial Grid record
'''
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname = "/GRID/RECORD/DATA/01jan2001:1200/01jan2001:1300/Ex9/"

with Open(dss_file) as fid:
    dataset = fid.read_grid(pathname)
    masked_array = dataset.read()
    gridinfo = dataset.profile
