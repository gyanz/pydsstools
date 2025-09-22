cdef enum pdc_mode:
    normal = 0
    allocate = 1
    one = 2

cdef PairedDataStruct createPDS(zStructPairedData *zpds):
    """Creates paired-data struct
    
    Returns
    -------
        # PairedDataStruct class

    Usage
    -----
        # Available only in extension scripts
    """
    pd_st = PairedDataStruct()
    if zpds:
            pd_st.zpds = zpds
    else:
        zstructFree(zpds)            
        zpds=NULL
    return pd_st

cdef class PairedDataStruct:
    """Paired-Data Struct class
    """

    cdef:
        zStructPairedData *zpds

    def __cinit__(self,*arg,**kwargs):
        self.zpds=NULL

    def __dealloc__(self):
        if self.zpds:
            zstructFree(self.zpds)
            #self.zpds=NULL


    def get_data(self):
        """Get paired data values
        
        Returns
        -------
            x,curves and labels_list
            x: cython array of x axis values which is common for all the curves
            curves: multidimension cython array with each row representing a curve
            labels_list: list containing names of the curves

        Notes
        -----
            * The row-column order of underlyign C array is just the reverse of the 
              row-column relationship used in pydsstools. In the C array, each
              row contains data for each curve. 
            * Paired data conventions is the first row is row 1 and the first
              column is column 1, not row 0 or column 0.        
        """
        cdef:
            int rows = self.rows
            int cols = self.cols
            view.array ca_view_xdata = view.array(shape=(1,rows), 
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

            view.array ca_view_ydata = view.array(shape=(cols,rows),
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

        ca_view_xdata.data = <char *>(self.zpds[0].floatOrdinates)
        ca_view_ydata.data = <char *>(self.zpds[0].floatValues)
        labels_list = self.labels
        return ca_view_xdata,ca_view_ydata,labels_list

    @property
    def x_data(self):
        cdef:
            int rows = self.rows
            int cols = self.cols
            view.array ca_view_xdata = view.array(shape=(1,rows), 
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

        ca_view_xdata.data = <char *>(self.zpds[0].floatOrdinates)
        return ca_view_xdata

    @property
    def y_data(self):
        cdef:
            int rows = self.rows
            int cols = self.cols
            view.array ca_view_ydata = view.array(shape=(cols,rows),
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

        ca_view_ydata.data = <char *>(self.zpds[0].floatValues)
        return ca_view_ydata

    @property
    def data_type(self):
        if self.zpds:
            return self.zpds[0].dataType

    @property
    def rows(self):
        """ 
        Return
            int: the total number of data per curve i.e. no of columns 
        """
        cdef:
            int count = 0
            int row_start,row_end

        if self.zpds:
            count = self.zpds[0].numberOrdinates
            row_start = self.zpds[0].startingOrdinate
            if row_start > 0:
                row_end = self.zpds[0].endingOrdinate
                count = row_end - row_start + 1

        return count

    @property
    def cols(self):
        """
        Returns
        ------
            int: the total number of curves i.e. no of rows
        """
        cdef:
            int count = 0
            int col_start,col_end

        if self.zpds:
            count = self.zpds[0].numberCurves
            col_start = self.zpds[0].startingCurve
            if col_start > 0:
                col_end = self.zpds[0].endingCurve
                count = col_end - col_start + 1

        return count 

    @property
    def shape(self):
        return (self.rows,self.cols)
    
    @property
    def row_start(self):
        """ 
        """
        cdef:
            int row_start

        if self.zpds:
            row_start = self.zpds[0].startingOrdinate -1
            return row_start 

    @property
    def row_end(self):
        """ 
        """
        cdef:
            int row_end

        if self.zpds:
            row_end = self.zpds[0].endingOrdinate - 1
            return row_end 

    @property
    def col_start(self):
        """ 
        """
        cdef:
            int col_start

        if self.zpds:
            col_start = self.zpds[0].startingCurve -1
            return col_start 

    @property
    def col_end(self):
        """ 
        """
        cdef:
            int col_end

        if self.zpds:
            col_end = self.zpds[0].endingCurve - 1
            return col_end 

    @property
    def x_units(self):
        if self.zpds:
            if self.zpds[0].unitsIndependent:
                return self.zpds[0].unitsIndependent 
        return ''

    @property
    def x_type(self):
        if self.zpds:
            if self.zpds[0].typeIndependent:
                return self.zpds[0].typeIndependent 
        return ''

    @property
    def y_units(self):
        if self.zpds:
            if self.zpds[0].unitsDependent:
                return self.zpds[0].unitsDependent 
        return ''

    @property
    def y_type(self):
        if self.zpds:
            if self.zpds[0].typeDependent:
                return self.zpds[0].typeDependent 
        return ''

    @property
    def y_labels(self):
        cdef:
            int label_length
            int col_start,col_end
            list labels
            bytes clabel

        col_start = self.col_start
        col_end = self.col_end
        labels = ['' for i in range(col_start,col_end+1)]

        if self.zpds:
            if self.zpds[0].labelsLength and self.zpds[0].labels:
                label_length = self.zpds[0].labelsLength
                clabel = <bytes>self.zpds[0].labels[:label_length]
                logging.debug("paired data raw labels = ({})".format(clabel))
                _labels = clabel.split(b"\x00")
                _labels = [x.decode().strip() for x in _labels]
                if _labels and _labels[-1] == "":
                    _labels = _labels[:-1]
                for i,label in enumerate(_labels):
                    labels[i] = label    

        return labels

cdef class PairedDataContainer:
    """PairedDataContainer(pathname,shape,**kwargs)

    Create paired data container that can be written to dss file.
    """

    cdef:
        str _pathname
        tuple _shape
        np.ndarray _xdata
        str _xunits
        str _xtype
        np.ndarray _ydata
        str _yunits
        str _ytype
        list _ylabels
        int _ylabel_len

        #public int curve_no
        #public int data_no
        #public str independent_units
        #public str independent_type
        #public str dependent_units 
        #public str dependent_type
        #public list labels_list
        #public object curves
        #public object independent_axis

        int _storage_flag # 10 or 11
        float[:] _xdata_mv
        float* _ydata_ptr
        float [:,::1] _ydata_mv
        bytearray _ylabels_bytes
        #int storageFlag # 10 or 11
        #float [:] independent_axis_mv
        #float [:,::1] curves_mv # delete this after saving to dss
        #float *curves_ptr
        #readonly bytearray labels
        #int labelsLength

    def __init__(self,pathname,shape,**kwargs):
        """PairedDataContainer(pathname,shape,**kwargs)
        
        """
        self.pathname = pathname

        if not isinstance(shape,(list,tuple)) and len(shape) == 2:
            raise TypeError(f"Expected list, tuple for shape argument, got {type(shape).__name__}")

        if not (isinstance(shape[0],int) and isinstance(shape[1],int)):
            raise TypeError(f"Expected int values 'shape', got {type(shape[0]).__name__}")

        if not (shape[0] >=1 and shape[1]>=1):
            raise TypeError(f"Expected positive values in shape, got {shape}")

        self._shape = shape    

        self.x_units = kwargs.pop("x_units",'')
        self.x_type = kwargs.pop("x_type",'linear')

        self.y_units = kwargs.pop("y_units",'')
        self.y_type = kwargs.pop("y_type",'linear')

        self.x_data = kwargs.pop('x_data',None)
        self.y_data = kwargs.pop('y_data',None)

        self.y_labels = kwargs.pop('y_labels',[])
        self._ylabel_len = max(kwargs.pop('label_size',12),12)

    @property
    def pathname(self):
        return self._pathname    

    @pathname.setter
    def pathname(self,value):
        if isinstance(value, str):
            self._pathname = value   
        elif isinstance(value, DssPathName):
            self._pathname = value.text()
        else:
            raise ValueError(f'Expected string or DssPathname for pathname, got {type(value).__name__}')        

    @property
    def shape(self):
        return self._shape    

    @property
    def rows(self):
        return self.shape[0]   

    @property
    def cols(self):
        return self.shape[1]

    @property
    def x_data(self):
        return self._xdata
    
    @x_data.setter
    def x_data(self,data):
        if data is not None:
            if isinstance(data,array.array):
                _xdata = np.asarray(data,np.float32)
                
            elif isinstance(data,np.ndarray):
                _xdata = np.ascontiguousarray(data,dtype=np.float32)

            elif isinstance(data,(list,tuple)):
                _xdata = np.array(data,np.float32)

            else:
                raise "Invalid Independent axis data container"  

            assert _xdata.shape[0] == self.rows, "Length of x_data or curves does not match the paired data shape[0]"

            self._xdata = _xdata
            self._xdata_mv = self._xdata    

    @property
    def x_units(self):
        return self._xunits

    @x_units.setter
    def x_units(self,data):
        self._xunits = data

    @property
    def x_type(self):
        return self._xtype
    
    @x_type.setter
    def x_type(self,data):
        self._xtype = data

    @property
    def y_data(self):
        return self._ydata

    @y_data.setter
    def y_data(self,data):
        if data is not None:
            if isinstance(data,np.ndarray):
                if data.ndim == 2:
                    _ydata = np.ascontiguousarray(data,dtype=np.float32)
                else:
                    raise BaseException("y_data must be 2 dimensional numpy array")

            elif isinstance(data,(list,tuple)):
                _ydata = np.asarray(data,np.float32)
                if _ydata.ndim == 1:
                    _ydata =_ydata.reshape(1,-1)
                elif _ydata.ndim > 2:    
                    raise BaseException("y_data must be 2D array, list or tuple")

            else:
                raise "Invalid y_data"  

            assert _ydata.shape[0] == self.cols, "Number of y_data or curves in y_data does not match the paired data shape[1]"
            assert _ydata.shape[1] == self.rows, "Length of y_data or curves does not match the paired data shape[0]"
            
            self._ydata = _ydata
            self._ydata_mv = self._ydata
            self._ydata_ptr = &self._ydata_mv[0,0]    

    @property
    def y_units(self):
        return self._yunits

    @y_units.setter
    def y_units(self,data):
        self._yunits = data

    @property
    def y_type(self):
        return self._ytype

    @y_type.setter
    def y_type(self,data):
        self._ytype = data

    @property
    def y_labels(self):
        return self._ylabels

    @y_labels.setter
    def y_labels(self,data):
        if not isinstance(data,(list,tuple)):
            raise TypeError(f"Expected list, tuple of string for y_labels argument, got {type(data).__name__}")

        if not all(isinstance(x, str) for x in data):
            raise ValueError("All elements of the y_labels must be strings")

        labels = ['' for x in range(self.cols)]
        for i,x in enumerate(data):
            labels[i] = data[i]

        self._ylabels = labels
    
    cdef set_clabels(self,pdc_mode mode,int curve_mode_ylabel_len=0):
        cdef:
            int cols
            str s
            list label,labels,rev_labels
            #bytearray label_byte_string

        cols = self.cols
        labels = self.y_labels
        label_byte_string = b''

        if mode == pdc_mode.normal:
            if all(s=='' for s in labels):
                labels = []
            if labels:
                label_byte_string = "\x00".join([x.encode('ascii') for x in labels]) + b'\x00'
        
        elif mode == pdc_mode.allocate:
            label_max_len = 0
            for label in labels:
                label_max_len = max(label_max_len,len(label))
            label_max_len = max(label_max_len, self._ylabel_len)

            rev_labels = []
            for label in labels:
                rev_label = '{0:<{1:d}s}'.format(label,label_max_len)
                rev_labels.append(rev_label)

            if rev_labels:
                label_byte_string = "\x00".join([x.encode('ascii') for x in rev_labels]) + b'\x00'
        
        else:
            if curve_mode_ylabel_len < 1:
                raise ValueError('Length of label of curve in the preallocated paired data is either not specified or invalid')

            if labels:
                label = '{0:<{1:d}s}'.format(labels[0],curve_mode_ylabel_len)[0:curve_mode_ylabel_len]
                label_byte_string = label.encode('ascii') + b'\x00'

        self._ylabel_bytes = bytearray(label_byte_string)        


cdef PairedDataStruct write_allocate_pdata(PairedDataContainer pdc):
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc._pathname
        float *x_data
        int rows = pdc.rows
        int cols = pdc.cols
        int label_length
        char *x_units = pdc._xunits
        char *x_type = pdc._xtype
        char *y_units = pdc._yunits
        char *y_type = pdc._ytype

    if pdc.x_data is None:
        raise ValueError('x_data for pair data is None')

    x_data = &pdc._xdata_mv[0]
    
    zpds = zstructPdNew(pathname)
    zpds[0].numberCurves = cols
    zpds[0].numberOrdinates = rows
    zpds[0].floatOrdinates = x_data
    zpds[0].doubleOrdinates = NULL
    zpds[0].unitsIndependent = x_units
    zpds[0].typeIndependent = x_type
    zpds[0].unitsDependent = y_units
    zpds[0].typeDependent = y_type

    if pdc._ylabels_bytes is not None:
        label_length = len(pdc._ylabels_bytes)
        zpds[0].labelsLength =label_length
        zpds[0].labels = <char *>pdc._ylabels_bytes

    pd_st = createPDS(zpds)

    return pd_st

cdef PairedDataStruct write_one_pdata(long long *ifltab,PairedDataContainer pdc,int col_index,int row_start=-1,int row_end=-1):
    '''

    column and row index are 0 based on python side while it is 1 based on the c code

    '''
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc._pathname
        float *y_data = NULL

    if pdc.y_data is None:
        raise ValueError('y_data for pair data is None')

    if pdc.ydata.shape[0] > 1 or pdc.y_data.shape[1] > pdc.rows:
        raise ValueError('y_data is not valid for writing single paired data curve')    

    if row_start == -1 and row_end == -1:
        # writes full curve or column data
        pass
    elif row_start < 0 or row_end > pdc.rows - 1:
        raise ValueError('row index for paired data is out of range')

    col_index += 1
    row_start += 1
    row_end += 1
    y_data = pdc._ydata_ptr    

    zpds = zstructPdNew(pathname)
    zpds[0].startingCurve = col_index
    zpds[0].endingCurve = col_index
    zpds[0].startingOrdinate = row_start
    zpds[0].endingOrdinate = row_end
    zpds[0].floatValues  = y_data
    zpds[0].floatOrdinates = NULL
    zpds[0].doubleOrdinates = NULL
    zpds[0].doubleValues  = NULL

    if pdc._ylabels_bytes is not None:
        label_length = len(pdc._ylabels_bytes)
        zpds[0].labelsLength = label_length
        zpds[0].labels = <char *>pdc._ylabels_bytes

    pd_st = createPDS(zpds)
    return pd_st
    
cdef PairedDataStruct write_normal_pdata(PairedDataContainer pdc):
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc._pathname
        float *x_data
        float *y_data
        int rows = pdc.rows
        int cols = pdc.cols
        int label_length
        char *x_units = pdc._xunits
        char *x_type = pdc._xtype
        char *y_units = pdc._yunits
        char *y_type = pdc._ytype

    if pdc.y_data is None:
        raise ValueError('y_data for pair data is None')

    if pdc.x_data is None:
        raise ValueError('x_data for pair data is None')

    x_data = &pdc._xdata_mv[0]
    y_data = pdc._ydata_ptr    

    zpds = zstructPdNewFloats(pathname, x_data, y_data, rows,
                              cols, x_units, x_type,
                              y_units, y_type)

    if pdc._ylabels_bytes is not None:
        label_length = len(pdc._ylabels_bytes)
        zpds[0].labelsLength = label_length
        zpds[0].labels = <char *>pdc._ylabels_bytes

    pd_st = createPDS(zpds)
    return pd_st
