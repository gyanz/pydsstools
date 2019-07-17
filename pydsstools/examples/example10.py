'''
Write Spatial Grid record

Notes:
    type options: PER-AVER, PER-CUM, INST-VAL,INST-CUM, FREQ, INVALID
    flipud: 1 (default) -  flips the numpy array upside down as dss array layout is opposite
            0 - numpy array array is stored as it is


'''
import numpy as np
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname_in = "/GRID/RECORD/DATA/01jan2001:1200/01jan2001:1300/Ex9/"
pathname_out = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10/"

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

