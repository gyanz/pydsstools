'''
Write Spatial Grid record

'''
import numpy as np
import numpy.ma as ma
from affine import Affine
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core.gridinfo import GridInfoCreate,GridType,DataType

dss7_file = "output\out7.dss"
dss6_file = "output\out6.dss"

pathname_out = "/GRID-VER{}/RECORD/DATA/01jan2019:1200/02jan2019:0000/Ex10a/"

# ======================================================================
# Write to DSS 7
# ======================================================================
with Open(dss7_file, mode="rw") as fid7, Open(dss6_file,version=6, mode="rw") as fid6:
    shape = (10,10)
    cell = 2000
    xmin,ymin = (2000,4000)

    data = np.reshape(np.array(range(100),dtype=np.float32),shape)
    data[0] = np.nan 
    ginfo = GridInfoCreate(grid_type = GridType.albers_time,
                           shape = shape,
                           cell_size = cell,
                           data_type= DataType.per_aver,
                           data_units='mm',
                           min_xy = (xmin,ymin)
                           )

    #ymax = ymin + cell * shape[0]
    #transform = Affine(cell,0,xmin,0,-cell,ymax)
    # ====================================
    # Write to DSS 7
    # ====================================
    fid7.put_grid(data,pathname_out.format('100'),ginfo)
    fid7.put_grid0(data,pathname_out.format('0'),ginfo)
    # ====================================
    # Write to DSS 6
    # ====================================
    fid6.put_grid0(data,pathname_out.format('0'),ginfo)
            

