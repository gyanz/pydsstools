'''
Write paired data-series
'''
from array import array
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import PairedDataContainer

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///WRITE/"

fid = HecDss.Open(dss_file)
pdc = PairedDataContainer()

pdc.pathname = pathname
pdc.curve_no = 1
pdc.independent_axis = array('f',[i/10.0 for i in range(1,10)])
pdc.data_no = len(pdc.independent_axis)
pdc.curves = np.array([range(1,10)],dtype=np.float32)
fid.put_pd(pdc)
fid.close()
