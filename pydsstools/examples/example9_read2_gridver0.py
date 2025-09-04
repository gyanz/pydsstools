'''
Read Spatial Grid record
'''
import logging
logging.basicConfig(level=logging.INFO)
import traceback
from pydsstools.heclib.dss.HecDss import Open

dss_file = "sample_dss\grid6.dss"

with Open(dss_file) as fid:
    # hrap data
    print("="*30)
    print("***Hrap grid***")
    print("="*30)
    pathname = r"/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD/"
    ar1,gridinfo1 = fid.read_grid2(pathname)
    print(gridinfo1)

    # albers data
    print("="*30)
    print("***Albers grid***")
    print("="*30)
    pathname = r"/SHG/MARFC/PRECIP/23JUL2003:2300/23JUL2003:2400/NEXRAD (2000 M)/"
    ar2,gridinfo2 = fid.read_grid2(pathname)
    print(gridinfo2)

    # specified data
    print("="*30)
    print("***Specified grid***")
    print("="*30)
    pathname = r"/UTM_18N/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD (1000 M)/"
    ar3,gridinfo3 = fid.read_grid2(pathname)
    print(gridinfo3)



