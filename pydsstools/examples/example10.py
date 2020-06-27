'''
Write Spatial Grid record

'''
import numpy as np
import numpy.ma as ma
from affine import Affine
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import gridInfo

dss_file = "example.dss"

pathname_out1 = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10a/"
pathname_out2 = "/GRID/RECORD/DATA/01jan2019:1200/01jan2019:1300/Ex10b/"

with Open(dss_file) as fid:
    # Type 1: data is numpy array
    # np.nan is considered as nodata
    data = np.reshape(np.array(range(100),dtype=np.float32),(10,10))
    data[0] = np.nan # assign nodata to first row
    grid_info = gridInfo()
    cellsize = 100 # feet
    xmin,ymax = (1000,5000) # grid top-left corner coordinates
    affine_transform = Affine(cellsize,0,xmin,0,-cellsize,ymax)
    grid_info.update([('grid_type','specified'),
                      ('grid_crs','unknown'),
                      ('grid_transform',affine_transform),
                      ('data_type','per-aver'),
                      ('data_units','mm'),
                      ('opt_time_stamped',False)])
    fid.put_grid(pathname_out1,data,grid_info)
            
    # Type 2: data is numpy masked array, where masked values are considered nodata
    data = np.reshape(np.array(range(100),dtype=np.float32),(10,10))
    data = ma.masked_where((data >= 10) & (data <30),data) # mask second and third rows
    fid.put_grid(pathname_out2,data,grid_info)

