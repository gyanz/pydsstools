from libc.stddef  cimport size_t
#from libc.stdint cimport int32_t

ctypedef enum NumKind:
    NUM_F32
    NUM_I32

cdef float* float_ref(float f) except NULL

cdef void set_cstring(char **dst, str py_s) except *

cdef int _nbytes_from_len(Py_ssize_t n, size_t itemsize, size_t* out) nogil

cdef void* calloc_checked(size_t count, size_t size) except NULL

cdef void calloc_copy_from_list(void** dst, size_t max_len, list values, NumKind kind) except *

cdef float* malloc_floats_from_ints(int[::1] a) except NULL