'''
Read paired data-series

Notes:
    Row and column/curve indices start at 1 (not zero)

'''
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/DATA/FREQ-FLOW///Ex5/"

#labels_list = ['Column 1','Elevens']

with HecDss.Open(dss_file) as fid:
    read_all = fid.read_pd(pathname)

    row1,row2 = (2,4)
    col1,col2 = (1,2)
    read_partial = fid.read_pd(pathname,window=(row1,row2,col1,col2))

