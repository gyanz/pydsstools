'''
Copy DSS-7 Grid to DSS-6 file using two approaches 

'''
import logging
logging.basicConfig(logging.INFO)
from pydsstools.heclib import gridv6
from pydsstools.heclib.dss.HecDss import Open

dss7_file = "example.dss"
dss6_file = "example_dss6.dss"

pathname_in = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/PRISM/"
pathname1_out = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/Ex16-Spatialgrid/"
pathname2_out = "/SHG/MAXTEMP/DAILY/08FEB1982:0000/08FEB1982:2400/Ex16-Array/"

with Open(dss_file) as fidin, Open(dss6_file,version=6) as fidout:
    dataset = fidin.read_grid(pathname_in)

    # Method 1: using the spatialgrid dataset
    fidout.put_grid6(pathname1_out,dataset)

    # Method 2: using the underlying data and gridinfo (remember to flip the array!)
    data = dataset.read().data
    profile = gridv6._convert_grid7_to_grid6_meta(dataset)
    fidout.put_grid6(pathname2_out,data,profile,flipud=1)
