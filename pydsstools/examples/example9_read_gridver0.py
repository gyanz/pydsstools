"""
Read Spatial Grid record
"""

import logging

logging.basicConfig(level=logging.INFO)
import traceback
from pydsstools.heclib.dss.HecDss import Open

dss_file = "sample_dss\grid6.dss"

with Open(dss_file) as fid:
    # hrap data
    print("=" * 30)
    print("***Hrap grid***")
    print("=" * 30)
    pathname = r"/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD/"
    ds = fid.read_grid(pathname)
    masked_array = ds.read()
    gridinfo1 = ds.gridinfo
    print(gridinfo1)
    print(">> Extra args <<")
    print(gridinfo1.extra_info)

    # albers data
    print("=" * 30)
    print("***Albers grid***")
    print("=" * 30)
    pathname = r"/SHG/MARFC/PRECIP/23JUL2003:2300/23JUL2003:2400/NEXRAD (2000 M)/"
    ds = fid.read_grid(pathname)
    masked_array = ds.read()
    gridinfo2 = ds.gridinfo
    print(gridinfo2)
    print(">> Extra args <<")
    print(gridinfo2.extra_info)

    # specified data
    print("=" * 30)
    print("***Specified grid***")
    print("=" * 30)
    pathname = r"/UTM_18N/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/NEXRAD (1000 M)/"
    ds = fid.read_grid(pathname, False)
    masked_array = ds.read()
    gridinfo3 = ds.gridinfo
    print(gridinfo3)
    print(">> Extra args <<")
    print(gridinfo3.extra_info)
