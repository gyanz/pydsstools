'''
Spatial Analysis on grid
'''
# Notes
# Experimental geospatial methods for grid
# Not 100% sure about gridinfo that is computed for the cropped grid esp. for SHG and HRAP
# Will apreaciate user feedbacks on this
# This example code was tested using the following libraries
# gdal 3.2.2
# matplotlib 3.4.4
# rasterio 1.2.1
# Potential rasterio issue with CRS
# https://github.com/mapbox/rasterio/blob/master/docs/faq.rst#why-cant-rasterio-find-projdb
# Unset PROJ_LIB environmental variable (i.e., SET PROJ_LIB= )

from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import BoundingBox

dss_file = "example.dss"

pathname = r"/SHG/LCOLORADO/PRECIP/02JAN2020:1500/02JAN2020:1600/Ex15/"
pathname_out = r"/SHG/LCOLORADO/PRECIP/02JAN2020:1500/02JAN2020:1600/Ex15 OUT/"

fid = Open(dss_file)
ds0 = fid.read_grid(pathname)

if not getattr(ds0,'raster',None) is None:
    ds0.raster.plot(mask_zeros = True, title = 'Original Spatial Grid')
    bbox = BoundingBox(400000,0,500000,100000)
    ds1 = ds0.raster.mask(bbox,crop = False)
    ds1.raster.plot(mask_zeros = True, title = 'Clipped Spatial Grid')
    ds2 = ds1.raster.mask(bbox,crop = True)
    ds2.raster.plot(mask_zeros = True, title = 'Cropped Spatial Grid')
    fid.put_grid(pathname_out,ds2)
