'''
Read Spatial Grid record
'''
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core import core_heclib

dss_file = "spatialgrid0.dss"

pathname = "/a/b/c/01jan2001:1200/01jan2001:1300/f/"

with Open(dss_file) as fid:
    dataset = fid.read_grid(pathname)
    profile = dataset.profile
    grid_array = dataset.read()
