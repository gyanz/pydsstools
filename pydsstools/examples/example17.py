'''
Test of Paired Data Series labels
'''

from pydsstools.heclib.dss import HecDss
from pydsstools.heclib.utils import dss_logging
dss_logging.config(level='None')


dss_file = "example.dss"
pathname ="/PAIRED/PREALLOCATED DATA/FREQ-FLOW///Ex7/"
rows,cols = (10,5)
fid = HecDss.Open(dss_file)


# 1. Allocate pds with fixed label size per column, default labels are 1,2,3,...
print('Test 1:')
label_size = 31
fid.preallocate_pd((rows,cols),pathname=pathname,label_size = label_size)
pds = fid.read_pd(pathname,dataframe=False)
pd_info = fid.pd_info(pathname)
print('pd_info = %r',pd_info)
print('labels in preallocated ods = %r',pds.labels)
assert len(pds.labels[0]) == label_size, "Allocated label size is incorrect"
print('Passed Test 1\n')

#2. Write to column 1, and update its default label 
print('Test 2:')
col = 1
data = [x*2 for x in range(rows)]
label = 'A'*40
fid.put_pd(data,curve_index=col,pathname=pathname,labels_list=[label])
pds = fid.read_pd(pathname,dataframe=False)
print('labels in preallocated pds = %r',pds.labels)
assert len(pds.labels[0]) == label_size, "PDS label was not correctly updated"
print('Passed Test 2\n')

#3. Write to column 2, but keep default label
print('Test 3:')
col = 2
data = [x*3 for x in range(rows)]
fid.put_pd(data,curve_index=col,pathname=pathname,labels_list=[])
pds = fid.read_pd(pathname,dataframe=False)
print('labels in preallocated pds = %r',pds.labels)
assert pds.labels[1].strip() == '2', "PDS label for column 2 is incorrect"
print('Passed Test 3')

fid.close()
