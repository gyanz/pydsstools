from pyproj import CRS
from . import HRAP_WKT, SHG_WKT 

ALBERS_WKT = SHG_WKT

SHG_WKT_CUSTOM = '''PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",\
GEOGCS[\"GCS_North_American_{0}\",DATUM[\"D_North_American_{0}\",\
SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],\
UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],\
PARAMETER[\"False_Easting\",{1}],PARAMETER[\"False_Northing\",{2}],\
PARAMETER[\"Central_Meridian\",{3}],PARAMETER[\"Standard_Parallel_1\",{4}],\
PARAMETER[\"Standard_Parallel_2\",{5}],PARAMETER[\"Latitude_Of_Origin\",{6}],\
UNIT[\"Meter\",1.0]]'''

ALBERS_WKT_CUSTOM = SHG_WKT_CUSTOM

HEC_SHG_CELLSIZE = (10000,5000,2000,1000,500,200,100,50,20,10) # meters
HEC_SHG_APART = ('SHG10K','SHG5K','SHG2K','SHG1K','SHG500','SHG200','SHG100','SHG50','SHG20','SHG10') # meters

def parse_crs(wkt):
    crs = CRS(wkt)
    crs = crs.to_dict()
    return crs

def extract_albers_params(wkt):
    crs = parse_crs(wkt)
    info = {}
    info['datum'] = crs['datum']  
    info['proj_units'] = crs['units']
    info['first_parallel'] = crs['lat_1']
    info['sec_parallel'] = crs['lat_2']
    info['central_meridian'] = crs['lon_0']
    info['lat_origin'] = crs['lat_0']
    info['false_easting'] = crs['x_0']
    info['false_northing'] = crs['y_0']
    return info

