'''
Read DSS-6 Grid record
Copy DSS-6 Grid to DSS-7 file 

'''
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import dss_logging
dss_logging.config(level='Diagnostic')

dss6_file = "example_dss6.dss"
dss7_file = "example.dss"

pathname_in = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/PRISM/"
pathname_out = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/Ex11/"

with Open(dss6_file) as fid:
    dataset = fid.read_grid(pathname_in)
    data = dataset.read()
    profile = dataset.profile

with Open(dss6_file) as fidin, Open(dss7_file) as fidout:
    dataset = fidin.read_grid(pathname_in)
    fidout.put_grid(pathname_out,dataset,compute_range = True) # recomputing range limit table
