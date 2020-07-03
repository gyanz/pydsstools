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

    cpdef tuple _shape(self):
        cdef:
            int data_no = 0
            int curve_no = 0

        if self.zpds:
            curve_no = self.zpds[0].numberCurves
            data_no = self.zpds[0].numberOrdinates
        return (data_no,curve_no)

    cpdef tuple shape(self):
        return (self.data_no(),self.curve_no())

    cpdef int curve_no(self):
        """
        Returns
        ------
            int: the total number of curves i.e. no of rows
        """
        cdef:
            int num = 0
            int start_curve,end_curve

        if self.zpds:
            num = self.zpds[0].numberCurves
            start_curve = self.zpds[0].startingCurve
            if start_curve:
                end_curve = self.zpds[0].endingCurve
                num = end_curve - start_curve + 1

        return num 
    
    cpdef int data_no(self):
        """ 
        Return
            int: the total number of data per curve i.e. no of columns 
        """
        cdef:
            int num = 0
            int start_ord,end_ord
        if self.zpds:
            num = self.zpds[0].numberOrdinates
            start_ord = self.zpds[0].startingOrdinate
            if start_ord:
                end_ord = self.zpds[0].endingOrdinate
                num = end_ord - start_ord + 1

        return num 

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
            int rows = self.curve_no()
            int cols = self.data_no()
            view.array ca_view_x = view.array(shape=(1,cols), 
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

            view.array ca_view_curves = view.array(shape=(rows,cols),
                                            itemsize=sizeof(float),format='f',
                                            allocate_buffer=False)

        ca_view_x.data = <char *>(self.zpds[0].floatOrdinates)
        ca_view_curves.data = <char *>(self.zpds[0].floatValues)
        labels_list = self.labels
        return ca_view_x,ca_view_curves,labels_list

    @property
    def labels(self):
        cdef:
            int labelsLength
            bytes labels

        if self.zpds:
            labelsLength = self.zpds[0].labelsLength
            labels = <bytes>self.zpds[0].labels[:labelsLength]
            labels_list = labels.split(b"\x00")
            labels_list = [x.decode() for x in labels_list if x]
            return labels_list

    @property
    def labels_list(self):
        if self.labels:
            return self.labels

    @property
    def dataType(self):
        if self.zpds:
            return self.zpds[0].dataType

    @property
    def independent_units(self):
        if self.zpds:
            if self.zpds[0].unitsIndependent:
                return self.zpds[0].unitsIndependent 
        return ''

    @property
    def independent_type(self):
        if self.zpds:
            if self.zpds[0].typeIndependent:
                return self.zpds[0].typeIndependent 
        return ''

    @property
    def dependent_units(self):
        if self.zpds:
            if self.zpds[0].unitsDependent:
                return self.zpds[0].unitsDependent 
        return ''

    @property
    def dependent_type(self):
        if self.zpds:
            if self.zpds[0].typeDependent:
                return self.zpds[0].typeDependent 
        return ''

cdef class PairedDataContainer:
    cdef:
        public str pathname
        public int curve_no
        public int data_no
        public str independent_units
        public str independent_type
        public str dependent_units 
        public str dependent_type
        public list labels_list
        public object curves
        public object independent_axis
        int storageFlag # 10 or 11
        float [:] independent_axis_mv
        float [:,::1] curves_mv # delete this after saving to dss
        float *curves_ptr
        readonly bytearray labels
        int labelsLength
        #public bytes null_separated_bytes       

    def __init__(self,**kwargs):
        _pathname = kwargs.get('pathname','')
        _curve_no = kwargs.get('curve_no',0) 
        _labels_list = kwargs.get('labels_list',[])
        _independent_units = kwargs.get('independent_units','feet')
        _independent_type = kwargs.get('independent_type','linear')
        _dependent_units = kwargs.get('dependent_units','feet')
        _dependent_type = kwargs.get('dependent_type','linear')
        self.pathname = _pathname
        self.curve_no = _curve_no
        self.labels_list = _labels_list
        self.independent_units = _independent_units
        self.independent_type = _independent_type
        self.dependent_units =_dependent_units
        self.dependent_type =_dependent_type

    cdef int setFloatData(self) except *:
        """
        """
        #logging.debug("Setting floatValues")
        if isinstance(self.curves,array.array):
            if self.curves.typecode == 'f':
                #self.floatValues=&self.curves_mv[0]
                #self.curves_ca = 
                raise "Python array input not implemented for Curve Array"
            else:
                raise "Invalid Curve Array Values (must be 32 bit float)"

        elif isinstance(self.curves,np.ndarray):
            if self.curves.ndim == 2: 
                self.curves_mv =  np.ascontiguousarray(self.curves,dtype=np.float32)
                '''
                if self.curves.dtype==np.float32:
                    self.curves_mv = self.curves
                else:
                    self.curves_mv = self.curves.astype(np.float32)
                '''

                self.curves_ptr = &self.curves_mv[0,0]
            else:
                raise BaseException("Curves data must be 2 dimensional numpy array")

        else:
            raise BaseException("Invalid Curve Data")

    cdef int setIndependentAxisValues(self) except *:
        if isinstance(self.independent_axis,array.array):
            self.independent_axis_mv = np.asarray(self.independent_axis,np.float32)
        elif isinstance(self.independent_axis,np.ndarray):
            self.independent_axis_mv = np.ascontiguousarray(self.independent_axis,dtype=np.float32)
            '''
            if self.independent_axis.dtype==np.float32:
                self.independent_axis_mv = self.independent_axis
            else:
                self.independent_axis_mv = self.independent_axis_mv.astype(np.float32)
            '''
        elif isinstance(self.independent_axis,(list,tuple)):
            self.independent_axis_mv = np.array(self.independent_axis,np.float32)

        else:
            raise "Invalid Independent axis data container"  

    cdef int setLabels(self,int mode = -1,int label_size = 0) except *:
        # label_size is necessary for preallocation of pd only
        # 0 means default allocation
        # positive value gives length of label characters per curve
        cdef:
            int curve_no = self.curve_no # total number of pd curves
            int total_label_size # length of character array allocated for pd  
            int lists_list_length

        labels_list_length = len(self.labels_list) # not necessary for mode = 0 

        if mode == 0:
            # preallocate mode
            # allocate the character array length for the labels!!
            byte_labels = []
            if labels_list_length == 0:
                label_name = ' '*label_size
                label_name = label_name.encode('ascii')
                for i in range(curve_no):
                    byte_labels.append(label_name)

            else:
                for i in range(curve_no):
                    label_name = self.labels_list[i]
                    label_name = '{0:<{1:d}s}'.format(label_name,label_size)[0:label_size]
                    byte_labels.append(label_name.encode('ascii'))

            null_separated_bytes = b"\x00".join(byte_labels)+b"\x00"
            # +1 for null byte separating the labels
            #self.labels = bytearray([0]*total_label_size)
            self.labels = bytearray(null_separated_bytes)
            self.labelsLength = len(self.labels)

        elif mode == 1:
            # single curve to preallocated pd
            if labels_list_length:
                label_name = self.labels_list[0]
                x = '{0:<{1:d}s}'.format(label_name,label_size)[0:label_size] 
                if x:
                    if isinstance(x,str):
                        _x = x.encode('ascii')
                    elif isinstance(x,bytes):
                        _x=x
                    else:
                        __x = str(x)
                        _x = __x.encode('ascii')

                    null_separated_bytes = _x+b"\x00"
                    byte_array = bytearray(null_separated_bytes)
                    self.labels = byte_array
                    self.labelsLength = len(byte_array)
            else:
                # Assigning labels does not makes sense, setting labelsLength = 0 should retain the current label
                self.labels = bytearray(' '.encode('ascii')+b"\x00")
                self.labelsLength = 0


        else:
            #normal mode
            byte_labels = []
            if curve_no == labels_list_length:
                for x in self.labels_list: 
                    if isinstance(x,str):
                        _x = x.encode('ascii')
                    elif isinstance(x,bytes):
                        _x=x
                    else:
                        __x = str(x)
                        _x = __x.encode('ascii')
                    byte_labels.append(_x)

                null_separated_bytes = b"\x00".join(byte_labels)+b"\x00"
                byte_array = bytearray(null_separated_bytes)
                self.labels = byte_array
                self.labelsLength = len(byte_array)

            else:
                print("WARN: number of labels does not match total curves")


    cdef int setValues(self,int mode = -1, int label_size = 0) except *:
        """
        mode
        -----
            preallocate = 0, 
            one curve to save in already preallocated pd = 1,
            normal = any integer except the above values

        """

        if mode == 0:
            # preallocate pd to store curves later
            # Requirements:
            #   pathname
            #   curve_no
            #   data_no
            #   independent_axis_mv
            #   independent_units    
            #   independent_type    
            #   dependent_units    
            #   dependent_type    
            assert self.curve_no >=1 and self.data_no >=1, "curve_no and data_no must be > 0"
            self.setLabels(mode=0, label_size = label_size)

        elif mode == 1:
            # Save one curve on the preallocated/normal dataset
            self.setFloatData()
            self.setLabels(mode=1,label_size = label_size)

        else:
            # normal pd
            assert self.curve_no >=1 and self.data_no >=1, "curve_no and data_no must be > 0"
            self.setFloatData()
            assert (self.curve_no * self.data_no) == self.curves_mv.size
            self.setLabels(mode=-1)

        if not mode == 1:
            # Except for mode ==1, set the independent axis C array
            self.setIndependentAxisValues()
            assert len(self.independent_axis_mv) == self.data_no
        return 0


cdef PairedDataStruct preallocNewPairedData(PairedDataContainer pdc):
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc.pathname
        float *independent_axis = &pdc.independent_axis_mv[0]
        int data_no = pdc.data_no
        int curve_no = pdc.curve_no
        char *independent_units = pdc.independent_units
        char *independent_type = pdc.independent_type
        char *dependent_units = pdc.dependent_units
        char *dependent_type = pdc.dependent_type

    zpds = zstructPdNew(pathname)
    zpds[0].numberCurves = curve_no
    zpds[0].numberOrdinates = data_no
    zpds[0].floatOrdinates = independent_axis
    zpds[0].doubleOrdinates = NULL
    zpds[0].unitsIndependent = independent_units
    zpds[0].typeIndependent = independent_type
    zpds[0].unitsDependent = dependent_units
    zpds[0].typeDependent = dependent_type

    # additional check
    if pdc.labelsLength>0:
        zpds[0].labelsLength = pdc.labelsLength
        zpds[0].labels = <char *>pdc.labels
    pd_st = createPDS(zpds)
    return pd_st

cdef PairedDataStruct createOnePairedData(long long *ifltab,PairedDataContainer pdc,int curve_index,int start_ord_index=0,int end_ord_index=0):
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc.pathname
        float *curves = pdc.curves_ptr

    zpds = zstructPdNew(pathname)
    zpds[0].startingCurve = curve_index
    zpds[0].endingCurve = curve_index
    if start_ord_index:
        zpds[0].startingOrdinate = start_ord_index
        zpds[0].endingOrdinate = end_ord_index

        
    zpds[0].floatValues  = curves
    zpds[0].floatOrdinates = NULL
    zpds[0].doubleOrdinates = NULL
    zpds[0].doubleValues  = NULL
    if pdc.labelsLength>0:
        zpds[0].labels=<char *>pdc.labels
        zpds[0].labelsLength = pdc.labelsLength

    pd_st = createPDS(zpds)
    return pd_st
    
cdef PairedDataStruct createNewFloatPairedData(PairedDataContainer pdc):
    cdef:
        zStructPairedData *zpds=NULL
        PairedDataStruct pd_st
        char *pathname = pdc.pathname
        float *independent_axis = &pdc.independent_axis_mv[0]
        float *curves = pdc.curves_ptr
        int data_no = pdc.data_no
        int curve_no = pdc.curve_no
        char *independent_units = pdc.independent_units
        char *independent_type = pdc.independent_type
        char *dependent_units = pdc.dependent_units
        char *dependent_type = pdc.dependent_type

    zpds = zstructPdNewFloats(pathname, independent_axis, curves, data_no,
                              curve_no, independent_units, independent_type,
                              dependent_units, dependent_type)
    # additional check
    if pdc.labelsLength>0:
        zpds[0].labelsLength = pdc.labelsLength
        zpds[0].labels = <char *>pdc.labels

    pd_st = createPDS(zpds)
    return pd_st
