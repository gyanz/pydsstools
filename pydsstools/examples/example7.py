'''
Pre-allocate paired data-series
'''
from pydsstools.heclib.dss import HecDss

dss_file = "example.dss"
pathname ="/PAIRED/PREALLOCATED DATA/FREQ-FLOW///Ex7/"

with HecDss.Open(dss_file) as fid:
    rows = 10
    curves = 15
    fid.preallocate_pd((rows,curves),pathname=pathname)
