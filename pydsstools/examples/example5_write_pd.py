'''
Write paired data-series
'''
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import PairedDataContainer

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///Ex5/"

pdc = PairedDataContainer()
pdc.pathname = pathname
pdc.curve_no = 2
pdc.independent_axis = list(range(1,10))
pdc.data_no = 9
pdc.curves = np.array([[5,50,500,5000,50000,10,100,1000,10000],
                       [11,11,11,11,11,11,11,11,11]],dtype=np.float32)
pdc.labels_list = ['Column 1','Elevens']
pdc.independent_units = 'Number'
pdc.dependent_units = 'Feet'

fid = HecDss.Open(dss_file)
fid.put_pd(pdc)
fid.close()
