'''
Pre-allocate paired data-series
'''
from array import array
from pydsstools.heclib.dss import HecDss
from pydsstools.core import PairedDataContainer

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///PREALLOC WRITE/"
max_column_label_len = 5

pdc = PairedDataContainer()
pdc.pathname = pathname
pdc.curve_no = 10
pdc.independent_axis = array('f',[i/10.0 for i in range(1,11)])
pdc.data_no = len(pdc.independent_axis)
pdc.labels_list=[chr(x) for x in range(65,65+10)]

fid = HecDss.Open(dss_file)
fid.prealloc_pd(pdc,max_column_label_len)
fid.close()
