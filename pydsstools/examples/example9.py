'''
Read Spatial Grid record
'''
import traceback
from pydsstools.heclib.dss.HecDss import Open

dss_file = "example.dss"

pathname = "/GRID/RECORD/DATA/01jan2001:1200/01jan2001:1300/Ex9/"

with Open(dss_file) as fid:
    dataset = fid.read_grid(pathname)
    masked_array = dataset.read()
    gridinfo = dataset.profile
    try:
        dataset.raster.define_crs(2868)
        dataset.raster.save_tiff(r'grid_dataset.tif')
        dataset.raster.plot()
    except AttributeError:
        print('rasterio and matplotlib optional libraries must be installed')
        traceback.print_exc()
    else:
        print('grid data saved as grid_dataset.tif')
