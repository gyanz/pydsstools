"""
 Open class object for HEC-DSS file
"""
__all__ = ['Open']

try:
    import pandas as pd
except:
    pd = None

try:
    import numpy as np
except:
    np = None

from pydsstools.core import Open as _Open
from pydsstools.core import getPathnameCatalog, deletePathname

class Open(_Open):
    def __init__(self,dssFilename,version=None):
        #version = HEC-DSS version  6 or 7, automatically selected based on
        #the existing file type. When version is not specified for new file,
        # version 7 is selected.
        super().__init__(dssFilename,version)

    def read_pd_df(self,pathname,dtype=None,copy=True):
        """Read paired data as pandas dataframe
        """
        pds = super().read_pd(pathname)
        x,curves,label_list = pds.get_data()
        tb = np.asarray(curves).T
        # The row in curves array contains curve data
        # Transpose causes the curve data to be in columns (for DataFrame purpose)
        if not label_list:
            for i in range(len(label_list)+1):
                label_list.append(' ')

        indx=list(x[0])
        df = pd.DataFrame(data=tb,index=indx,columns=label_list,dtype=dtype,copy=copy) #copy=True is necessary
        df.index.name="X"
        return df

    read_pd = read_pd_df

    def getPathnameList(self,pathname,sort=0):
        # pathname string which can include wild card * for defining pattern
        catalog = getPathnameCatalog(self,pathname,sort)
        path_list = catalog.getPathnameList()
        return path_list

    def deletePathname(self,pathname):
        status = deletePathname(self,pathname)
        return status
