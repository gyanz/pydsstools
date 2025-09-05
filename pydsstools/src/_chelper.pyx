
ctypedef enum NumKind:
    NUM_F32
    NUM_I32

cdef float* float_ref(float f) except NULL:
    """ Helper function to allocate given float in heap and return its reference
    """
    cdef:
        float *p
    p = <float*>malloc(sizeof(float))
    if p == NULL:
        raise MemoryError('Unable to allocate memory for float')
    #*p = f
    p[0] = <float>f
    return p

cdef void set_cstring(char **dst, str py_s) except *:
    """
    Copy Python str -> UTF-8 C string.
    Precondition: *dst must be NULL (this function does not free old memory).
    Empty string keeps *dst = NULL (no allocation).
    """
    cdef const char* src
    cdef Py_ssize_t n = 0
    cdef char* p

    if dst[0] != NULL:
        raise ValueError("*dst must be NULL before assignment (owner frees).")

    src = PyUnicode_AsUTF8AndSize(py_s, &n)
    if src == NULL:
        # propagate the Python exception already set above
        return  

    if n == 0:
        dst[0] = NULL
        return

    p = <char*> malloc(<size_t> n + 1)
    if p == NULL:
        raise MemoryError('Unable to allocate memory for c string')

    memcpy(p, src, <size_t> n)
    p[n] = 0
    dst[0] = p

cdef inline int _nbytes_from_len(Py_ssize_t n, size_t itemsize, size_t* out) nogil:
    if n < 0:
        return -1
    if itemsize != 0 and <size_t>n > SIZE_MAX // itemsize:
        return -1
    out[0] = (<size_t>n) * itemsize
    return 0

cdef void* calloc_checked(size_t count, size_t size) except NULL:
    """
    Overflow-checked calloc. Returns NULL and raises MemoryError on failure.
    """
    cdef:
        void* p
    if size != 0 and count > SIZE_MAX // size:
        raise MemoryError("Allocation would be too big")
    p = calloc(count, size)
    if p == NULL:
        raise MemoryError("Unable to allocate memory")
    return p


# ---- generalized copier: supports float32 and int32 ----
cdef void calloc_copy_from_list(void** dst, size_t max_len, list values, NumKind kind) except *:
    """
    Allocates *dst with calloc(max_len, sizeof(T)) and copies len(values) elements.
    *dst must be NULL on entry. If values is empty, leaves *dst = NULL (no alloc).
    Raises:
      - ValueError if *dst is non-NULL, dst is NULL, or len(values) > max_len
      - MemoryError on overflow / allocation failure
    """
    if dst == NULL:
        raise ValueError("dst pointer is NULL")
    if dst[0] != NULL:
        raise ValueError("*dst must be NULL before assignment (owner frees).")

    cdef:
        carray ar
        float[::1] srcf
        int32_t [::1] srci
        Py_ssize_t n
        size_t nbytes
        void* p

    if kind == NUM_F32:
        ar = py_array.array('f', values)     # coerces ints->float32
        n = len(ar)
        if n == 0:
            dst[0] = NULL
            return
        if <size_t>n > max_len:
            raise ValueError("len(values) exceeds max_len")
        if _nbytes_from_len(n, sizeof(float), &nbytes) != 0:
            raise MemoryError("Byte-size overflow for copy")
        p = calloc_checked(max_len, sizeof(float))
        srcf = ar
        memcpy(p, &srcf[0], nbytes)

    elif kind == NUM_I32:
        # Ensure array('i') is 32-bit on this platform
        if py_array.array('i').itemsize != sizeof(int32_t):
            raise ValueError("array('i') is not 32-bit on this platform")
        ar = py_array.array('i', values)     # coerces floats->int via truncation
        n = len(ar)
        if n == 0:
            dst[0] = NULL
            return
        if <size_t>n > max_len:
            raise ValueError("len(values) exceeds max_len")
        if _nbytes_from_len(n, sizeof(int32_t), &nbytes) != 0:
            raise MemoryError("Byte-size overflow for copy")
        p = calloc_checked(max_len, sizeof(int32_t))
        srci = ar
        memcpy(p, &srci[0], nbytes)

    else:
        raise ValueError("unsupported kind")

    dst[0] = p

cdef float* malloc_floats_from_ints(int[:] a) except NULL:
    """
    Allocate a float* of length len(a) and copy with numeric conversion.
    Caller owns the returned pointer and must free(p).
    Empty input -> returns NULL (no allocation, no error).
    """
    cdef:
        float* p
        Py_ssize_t n = a.shape[0]
        Py_ssize_t i

    if n == 0:
        return NULL

    p = <float*> malloc(<size_t> n * sizeof(float))
    if p == NULL:
        raise MemoryError()

    for i in range(n):
        p[i] = <float> a[i]      # numeric conversion per element
    return p