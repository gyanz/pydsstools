cdef ArrayStruct createArrayStruct(zStructArray *zarr):
    arr_st = ArrayStruct()
    if zarr:
        arr_st.zarr = zarr
    else:
        zstructFree(zarr)
        zarr = NULL
    return arr_st


cdef class ArrayStruct:
    """Low-level wrapper around a C zStructArray returned by zarrayRetrieve."""

    cdef:
        zStructArray *zarr

    def __cinit__(self):
        self.zarr = NULL

    def __dealloc__(self):
        if self.zarr:
            zstructFree(self.zarr)

    @property
    def int_array(self):
        """numpy int32 array, or None if not present."""
        cdef:
            int n
            view.array ca
        if self.zarr and self.zarr[0].numberIntArray > 0 and self.zarr[0].intArray != NULL:
            n = self.zarr[0].numberIntArray
            ca = view.array(shape=(n,), itemsize=sizeof(int), format='i',
                            allocate_buffer=False)
            ca.data = <char *>self.zarr[0].intArray
            return np.asarray(ca)
        return None

    @property
    def float_array(self):
        """numpy float32 array, or None if not present."""
        cdef:
            int n
            view.array ca
        if self.zarr and self.zarr[0].numberFloatArray > 0 and self.zarr[0].floatArray != NULL:
            n = self.zarr[0].numberFloatArray
            ca = view.array(shape=(n,), itemsize=sizeof(float), format='f',
                            allocate_buffer=False)
            ca.data = <char *>self.zarr[0].floatArray
            return np.asarray(ca)
        return None

    @property
    def double_array(self):
        """numpy float64 array, or None if not present."""
        cdef:
            int n
            view.array ca
        if self.zarr and self.zarr[0].numberDoubleArray > 0 and self.zarr[0].doubleArray != NULL:
            n = self.zarr[0].numberDoubleArray
            ca = view.array(shape=(n,), itemsize=sizeof(double), format='d',
                            allocate_buffer=False)
            ca.data = <char *>self.zarr[0].doubleArray
            return np.asarray(ca)
        return None

    @property
    def data_type(self):
        if self.zarr:
            return self.zarr[0].dataType
        return None

    @property
    def dtype(self):
        """dtype of the populated sub-array(s).

        DSS-7 records (``data_type == 90``) can hold int, float, and double
        arrays simultaneously, so this property returns a list of strings —
        e.g. ``['int32', 'float32', 'float64']`` — one entry per populated
        sub-array.

        DSS-6 records (``data_type`` in 91/92/93) hold exactly one type, so
        this property returns a plain string: ``'int32'``, ``'float32'``, or
        ``'float64'``.

        Returns ``None`` if the struct is empty or the data type is unknown.
        """
        if not self.zarr:
            return None
        cdef int dt = self.zarr[0].dataType
        # DSS-6: one authoritative type per record
        if dt == ARRAY_TYPE_INT:
            return 'int32'
        if dt == ARRAY_TYPE_FLOAT:
            return 'float32'
        if dt == ARRAY_TYPE_DOUBLE:
            return 'float64'
        # DSS-7: inspect each sub-array independently
        if dt == ARRAY_TYPE_MIXED:
            result = []
            if self.zarr[0].numberIntArray > 0 and self.zarr[0].intArray != NULL:
                result.append('int32')
            if self.zarr[0].numberFloatArray > 0 and self.zarr[0].floatArray != NULL:
                result.append('float32')
            if self.zarr[0].numberDoubleArray > 0 and self.zarr[0].doubleArray != NULL:
                result.append('float64')
            return result if result else None
        return None

    @property
    def pathname(self):
        if self.zarr and self.zarr[0].pathname:
            return self.zarr[0].pathname
        return None


cdef class ArrayContainer:
    """Container for array data to be written to a DSS array record.

    Parameters
    ----------
    pathname : str
        DSS pathname for the record.
    int_array : array-like or None, optional
        Integer values to store. Converted to int32.
    float_array : array-like or None, optional
        Float values to store. Converted to float32.
    double_array : array-like or None, optional
        Double values to store. Converted to float64.

    Notes
    -----
    At least one of the three arrays must be provided.
    """

    cdef:
        str _pathname
        np.ndarray _int_array
        np.ndarray _float_array
        np.ndarray _double_array

    def __init__(self, pathname, int_array=None, float_array=None, double_array=None):
        if not isinstance(pathname, str):
            raise ValueError(f'Expected str for pathname, got {type(pathname).__name__}')
        if int_array is None and float_array is None and double_array is None:
            raise ValueError('At least one of int_array, float_array, double_array must be provided')
        self._pathname = pathname
        self._int_array = (np.ascontiguousarray(int_array, dtype=np.int32)
                           if int_array is not None else None)
        self._float_array = (np.ascontiguousarray(float_array, dtype=np.float32)
                             if float_array is not None else None)
        self._double_array = (np.ascontiguousarray(double_array, dtype=np.float64)
                              if double_array is not None else None)

    @property
    def pathname(self):
        return self._pathname

    @property
    def int_array(self):
        """numpy int32 array, or None if not provided."""
        return self._int_array

    @property
    def float_array(self):
        """numpy float32 array, or None if not provided."""
        return self._float_array

    @property
    def double_array(self):
        """numpy float64 array, or None if not provided."""
        return self._double_array


cdef ArrayStruct _build_array_struct(ArrayContainer arr):
    """Build a zStructArray from an ArrayContainer for writing.

    Data pointers reference the numpy arrays inside arr; arr must outlive
    the returned struct (guaranteed when called from _put_array).
    """
    cdef:
        zStructArray *zarr = NULL
        char *pathname = arr._pathname

    zarr = zstructArrayNew(pathname)

    if arr._int_array is not None:
        zarr[0].intArray = <int *>cnp.PyArray_DATA(arr._int_array)
        zarr[0].numberIntArray = arr._int_array.shape[0]

    if arr._float_array is not None:
        zarr[0].floatArray = <float *>cnp.PyArray_DATA(arr._float_array)
        zarr[0].numberFloatArray = arr._float_array.shape[0]

    if arr._double_array is not None:
        zarr[0].doubleArray = <double *>cnp.PyArray_DATA(arr._double_array)
        zarr[0].numberDoubleArray = arr._double_array.shape[0]

    return createArrayStruct(zarr)
