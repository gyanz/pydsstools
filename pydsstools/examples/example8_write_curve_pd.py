'''
Write individual curve data in pre-allocated paired data-series
'''
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/PREALLOCATED DATA/FREQ-FLOW///Ex7/"

with HecDss.Open(dss_file) as fid:
    curve_index = 5
    curve_label = 'Column 5'
    curve_data = [10,20,30,40,50,60,70,80,90,100]
    fid.put_pd(curve_data,curve_index,pathname=pathname,labels_list=[curve_label])

    curve_index = 2
    curve_label = 'Column 2'
    curve_data = [41,56,60]
    row1,row2 = (5,7)
    fid.put_pd(curve_data,curve_index,window = (row1,row2),
            pathname=pathname,labels_list=[curve_label])

