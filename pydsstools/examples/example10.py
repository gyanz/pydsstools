'''
Write Spatial Grid record
'''
import numpy as np
from pydsstools.heclib.dss.HecDss import Open

dss_file = "spatialgrid0.dss"

pathname_in = "/a/b/c/01jan2001:1200/01jan2001:1300/f/"
pathname_out = "/a/b/c/01jan2001:1200/01jan2001:1300/write/"

with Open(dss_file) as fid:
    # get shape and profile from example grid dss record
    dataset_in = fid.read_grid(pathname_in)
    profile_in = dataset_in.profile
    grid_in = dataset_in.read()

    # create random array, update profile and save as grid record
    profile_out = profile_in.copy()
    profile_out.update(type="PER-AVER",nodata=0,transform=dataset_in.transform) # required parameters
    profile_out.update(crs="UNDEFINED",units="ft",tzid="",tzoffset=0,datasource='') # optional parameters
    grid_out = np.random.rand(*grid_in.shape)*100
    fid.put_grid(pathname_out,grid_out,profile_out,flipud=1)

    # NOTES:
    #   type options: PER-AVER, PER-CUM, INST-VAL,INST-CUM, FREQ, INVALID
    #   flipud: 1 (default) -  flips the numpy array upside down as dss array layout is opposite
    #           0 - numpy array array is stored as is
